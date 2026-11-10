# Runs the standalone randomizer engine for bosses, princesses and companions, fed by the Archipelago slot
# Loot and drops stay with Archipelago so the engine only rolls fights, rooms and recruits

module BSAP
  BOOK_RANGE = 273..304

  def self.opt(name)
    @opts && @opts[name]
  end

  def self.set_opts(opts)
    @opts = opts
  end

  def self.books_shuffled?
    active? && opt("books_shuffled") == "true"
  end

  def self.books_needed
    n = opt("books_needed").to_i
    n > 0 ? [n, Rando::BOOKS_ALL].min : Rando::BOOKS_ALL
  end

  def self.rando_params
    return nil unless active? && opt("rando_seed")
    on = lambda { |k| opt(k) == "true" }
    rooms = opt("rooms").to_s.split(",").map(&:to_i)
    rooms = [0, 1, 2, 3] unless rooms.sort == [0, 1, 2, 3]
    { :seed => opt("rando_seed").to_i, :rooms => rooms, :books => on.call("books_shuffled"),
      :princesses => on.call("shuffle_princesses"), :companions => on.call("shuffle_companions"),
      :bosses => on.call("boss_shuffle"), :scaling => on.call("boss_scaling"),
      :enemies => on.call("enemy_shuffle"), :prologue => opt("shuffle_prologue") ? on.call("shuffle_prologue") : true,
      :special => on.call("special_boss_shuffle") }
  end
end

module Rando
  def self.settings
    { :enabled => false }
  end

  def self.save_settings
  end

  def self.data
    return nil unless $game_system
    return $game_system.rando if $game_system.rando
    BSAP.refresh_session
    params = BSAP.rando_params
    return nil unless params
    $game_system.rando = ap_roll(params)
    apply_data
    $game_system.rando
  end

  def self.ap_roll(p)
    opts = { :seed => p[:seed], :loot => false, :drops => false, :books => p[:books], :covenants => false,
             :princesses => p[:princesses], :bosses => p[:bosses], :special => p[:special], :scaling => p[:scaling],
             :enemies => p[:enemies], :prologue => p[:prologue], :companions => p[:companions],
             :books_needed => BSAP.books_needed }
    out = { :version => VERSION, :seed => p[:seed], :opts => opts, :place => {}, :spoiler => [], :drops => [],
            :beauty_carries => !p[:books], :archipelago => true }
    out[:rooms] = p[:rooms]
    out[:persona] = roll_persona(opts)
    out[:swaps] = roll_swaps(opts, out[:rooms], out[:persona])
    place_witch_flame(out) unless p[:books]
    out
  end

  # the slot decides, not the number the world was rolled with
  def self.books_needed
    BSAP.active? ? BSAP.books_needed : BOOKS_ALL
  end

  # every page remembers where it came from so a check inside a moved princess keeps its key
  def self.moved_princess(who, room, old)
    home = RandoData::PRINCESSES[who]
    ev = source_event(who)
    ev.pages.each_with_index { |pg, i| pg.instance_variable_set(:@bsap_src, "#{home[:map]}:#{home[:ev]}:#{i}") }
    ev.id = old.id
    ev.x = old.x
    ev.y = old.y
    if who == SNOW_WHITE
      before = ev.pages.dup
      add_snow_scene(ev)
      ev.pages.each { |pg| pg.instance_variable_set(:@bsap_src, nil) unless before.any? { |b| b.equal?(pg) } }
    end
    ev.pages.each do |page|
      page.list.each do |c|
        retarget(c, home[:ev])
        retarget_transfer(c, room) if who == MERMAID
      end
    end
    ev
  end
end

class Game_Troop
  alias bsap_book_make_drop_items make_drop_items
  def make_drop_items
    items = bsap_book_make_drop_items
    return items unless BSAP.books_shuffled?
    items.reject { |i| i.is_a?(RPG::Item) && BSAP::BOOK_RANGE.include?(i.id) }
  end
end
