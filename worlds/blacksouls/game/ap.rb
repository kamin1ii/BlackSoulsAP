# Archipelago bridge for BLACK SOULS
# The client writes session.txt and inbox.txt and this script writes checks.txt

module BSAP
  DIR = "Archipelago"
  SESSION = DIR + "/session.txt"
  INBOX = DIR + "/inbox.txt"
  CHECKS = DIR + "/checks.txt"
  ENDINGS = { 442 => "A", 443 => "B", 444 => "C", 456 => "D" }
  # a fight reached another way still counts for the boss of that arena
  SECOND_FIGHTS = { 315 => 161, 310 => 136 }
  # the switch the game turns on when she dies by any route counts for the boss fight that kills her
  # Elisabeth, Jeanne, the Golden Goose, the Crestfallen Hero, Marianna and the Talking Flower
  DEATH_SWITCHES = { 164 => 164, 211 => 227, 159 => 226, 169 => 201, 555 => 309, 174 => 306 }
  SLOT_FIGHT_BASE = 10000

  @locs = {}
  @scouts = {}
  @mirrors = {}
  @boss_checks = {}
  @server_done = {}
  @opts = {}
  @seed = nil
  @session_mtime = nil
  @inbox_mtime = nil
  @inbox = []

  def self.active?
    !@seed.nil?
  end

  def self.seed
    @seed
  end

  def self.read_lines(path)
    return nil unless File.exist?(path)
    data = File.open(path, "rb") { |f| f.read }
    data.force_encoding("UTF-8")
    data.split(/\r?\n/)
  rescue StandardError
    nil
  end

  def self.mtime(path)
    File.exist?(path) ? File.mtime(path) : nil
  rescue StandardError
    nil
  end

  def self.refresh_session
    m = mtime(SESSION)
    return if m.nil? || m == @session_mtime
    lines = read_lines(SESSION)
    return unless lines && lines.last == "end"
    @session_mtime = m
    @locs = {}
    @scouts = {}
    @mirrors = {}
    @boss_checks = {}
    @server_done = {}
    @opts = {}
    lines.each do |line|
      f = line.split("\t")
      case f[0]
      when "seed" then @seed = f[1]
      when "loc" then @locs[f[1]] = true
      when "scout" then @scouts[f[1]] = f[2]
      when "boss" then @boss_checks[f[1].to_i] = true
      when "done" then @server_done[f[1]] = true
      when "opt" then @opts[f[1]] = f[2].to_s
      when "mirror" then (@mirrors[f[1].to_i] ||= []) << [f[2].to_i, f[3].to_i, f[4].to_i, f[5].to_i, f[6]]
      end
    end
  end

  def self.loc?(key)
    @locs[key]
  end

  # done here or already counted by the server, for example from another save
  def self.done?(key)
    @server_done[key] || ($game_system && $game_system.bsap_checked[key]) ? true : false
  end

  def self.set_server_done(keys)
    keys.each { |k| @server_done[k] = true }
  end

  def self.scout(key)
    @scouts[key]
  end

  def self.mirrors(map_id)
    @mirrors[map_id] || []
  end

  def self.take_mirror(key)
    check(key)
    popup(scout(key) || "Archipelago item", "Item sent")
  end

  def self.boss_check?(troop_id)
    @boss_checks[troop_id]
  end

  def self.death(switch_id)
    troop = DEATH_SWITCHES[switch_id]
    check("boss:#{troop}") if troop && active? && boss_check?(troop)
  end

  # a death from before the session started, or from an older version of this script
  def self.sync_deaths
    return unless $game_switches
    DEATH_SWITCHES.each_key do |s|
      death(s) if $game_switches[s]
    end
  end

  def self.check(key)
    return unless $game_system
    list = $game_system.bsap_checked
    return if list[key]
    list[key] = true
    write_checks
  end

  def self.write_checks
    return unless $game_system && active?
    Dir.mkdir(DIR) unless File.directory?(DIR)
    body = $game_system.bsap_checked.keys.join("\n") + "\nend\n"
    File.open(CHECKS, "wb") { |f| f.write(body) }
  rescue StandardError
    nil
  end

  def self.pending_items
    m = mtime(INBOX)
    if m && m != @inbox_mtime
      lines = read_lines(INBOX)
      if lines && lines.last == "end"
        @inbox_mtime = m
        @inbox = lines[0...-1].map { |l| l.split("\t") }
      end
    end
    start = $game_system.bsap_received
    @inbox.select { |f| f[0].to_i >= start }
  end

  def self.popup(big, small, type = 5, value = 0)
    return unless $game_temp && $game_temp.streffect
    $game_temp.streffect.push(Window_Getinfo.new(big, type, small, value))
  end

  def self.give(kind, id, amount, sender)
    type = { "item" => 0, "weapon" => 1, "armor" => 2 }[kind]
    return if type.nil?
    if SceneManager.scene_is?(Scene_Map) && $game_temp.streffect
      popup(id, "From " + sender, type, amount)
    else
      table = [$data_items, $data_weapons, $data_armors][type]
      $game_party.gain_item(table[id], amount)
    end
  end

  def self.update_map
    refresh_session
    return unless active?
    ENDINGS.each { |id, letter| check("ending:" + letter) if $game_switches[id] }
    return if $game_map.interpreter.running? || $game_message.busy?
    shown = 0
    pending_items.each do |f|
      break if shown >= 3
      give(f[1], f[2].to_i, f[3].to_i, f[4].to_s)
      $game_system.bsap_received = f[0].to_i + 1
      shown += 1
    end
  end
end

class Game_Switches
  alias bsap_set []=
  def []=(switch_id, value)
    bsap_set(switch_id, value)
    letter = BSAP::ENDINGS[switch_id]
    BSAP.check("ending:" + letter) if value && letter && BSAP.active?
    BSAP.death(switch_id) if value
  end
end

class Game_System
  attr_writer :bsap_received

  def bsap_checked
    @bsap_checked ||= {}
  end

  def bsap_received
    @bsap_received ||= 0
  end
end

class Game_Temp
  attr_accessor :bsap_troop
end

class Game_Event
  def bsap_rpg_event
    @event
  end
end

class Game_Interpreter
  def bsap_key
    return nil if @event_id.nil? || @event_id <= 0 || @map_id != $game_map.map_id
    ev = $game_map.events[@event_id]
    return nil unless ev
    pages = ev.bsap_rpg_event.pages
    page = pages.index { |pg| pg.list.equal?(@list) }
    return nil unless page
    src = pages[page].instance_variable_get(:@bsap_src)
    return "#{src}:#{@index}" if src
    "#{@map_id}:#{@event_id}:#{page}:#{@index}"
  end

  def bsap_location?
    return false unless BSAP.active? && @params[1] == 0 && @params[2] == 0
    key = bsap_key
    return false unless key && BSAP.loc?(key)
    BSAP.check(key)
    BSAP.popup(BSAP.scout(key) || "Archipelago item", "Item sent")
    true
  end

  alias bsap_command_126 command_126
  def command_126
    return if bsap_location?
    bsap_command_126
  end

  alias bsap_command_127 command_127
  def command_127
    return if bsap_location?
    bsap_command_127
  end

  alias bsap_command_128 command_128
  def command_128
    return if bsap_location?
    bsap_command_128
  end

  # the arena is noted before the randomizer swaps who is fought there
  alias bsap_command_301 command_301
  def command_301
    unless $game_party.in_battle
      $game_temp.bsap_troop = BSAP.active? && @params[0] == 0 ? @params[1] % BSAP::SLOT_FIGHT_BASE : nil
    end
    bsap_command_301
  end
end

class Game_Map
  MIRROR_BASE_ID = 9000

  alias bsap_setup_events setup_events
  def setup_events
    bsap_setup_events
    BSAP.refresh_session
    return unless BSAP.active?
    BSAP.sync_deaths
    BSAP.mirrors(@map_id).each_with_index do |m, i|
      next if $game_system.bsap_checked[m[4]]
      source = load_data(sprintf("Data/Map%03d.rvdata2", m[2])).events[m[3]] rescue nil
      next unless source
      ev = Marshal.load(Marshal.dump(source))
      ev.id = MIRROR_BASE_ID + i
      ev.x = m[0]
      ev.y = m[1]
      ev.pages[0].list = [
        RPG::EventCommand.new(355, 0, ["BSAP.take_mirror(#{m[4].inspect})"]),
        RPG::EventCommand.new(123, 0, ["A", 0]),
        RPG::EventCommand.new
      ]
      @events[ev.id] = Game_Event.new(@map_id, ev)
    end
    refresh_tile_events if respond_to?(:refresh_tile_events, true)
  end
end

module BattleManager
  class << self
    alias bsap_process_victory process_victory
    def process_victory
      troop = $game_temp.bsap_troop
      troop = BSAP::SECOND_FIGHTS[troop] || troop if troop
      if troop && BSAP.active? && BSAP.boss_check?(troop)
        BSAP.check("boss:#{troop}")
      end
      bsap_process_victory
    end

    alias bsap_battle_end battle_end
    def battle_end(result)
      bsap_battle_end(result)
      $game_temp.bsap_troop = nil
    end
  end
end

class Scene_Map
  alias bsap_start start
  def start
    bsap_start
    BSAP.refresh_session
    BSAP.write_checks
  end

  alias bsap_update update
  def update
    bsap_update
    @bsap_tick = (@bsap_tick || 0) + 1
    if @bsap_tick >= 20
      @bsap_tick = 0
      BSAP.update_map
    end
  end
end
