# Direct connection for the mkxp-z build of the game
# Uses archipelago_rb and the RPGMaker VX Ace AP kit by EggSlashEther (MIT)

module BSAPNet
  CONFIG = "archipelago.json"
  DATA = "Archipelago/data.json"
  ENDING_GOALS = { 1 => "A", 2 => "B", 3 => "C", 4 => "D" }
  RETRY_SECONDS = 15

  def self.wanted?
    defined?(System) && File.exist?(CONFIG) && File.exist?(DATA)
  end

  def self.setup
    ruby_dir = File.join(Dir.pwd, "Ruby")
    $:.push(ruby_dir)
    Dir.glob(File.join(ruby_dir, "**", "*")).each { |path| $:.push(path) if File.directory?(path) }
    require "archipelago_rb"
    require "json"
    data = JSON.parse(File.read(DATA))
    @key_to_id = data["locations"]
    @id_to_keys = {}
    @key_to_id.each { |key, id| (@id_to_keys[id] ||= []) << key }
    @item_table = data["items"]
    @mirror_table = data["mirrors"]
    @net_items = []
    @messages = []
    @connected = false
    @need_sync = false
    true
  rescue StandardError, LoadError => e
    @setup_error = e.message
    false
  end

  def self.connect
    cfg = JSON.parse(File.read(CONFIG))
    @connected = false
    @last_attempt = Time.now
    @client = Archipelago::Client.new
    info = @client.connect_info
    info["game"] = "Black Souls"
    info["items_handling"] = 7
    info["tags"] = []
    info["hostname"] = cfg["hostname"].to_s.empty? ? "archipelago.gg" : cfg["hostname"].to_s
    info["port"] = cfg["port"].to_i
    info["name"] = cfg["name"].to_s
    info["password"] = cfg["password"].to_s
    # the library's own refusal handler raises, replace it with one that reports the reason
    @client.instance_variable_get(:@listeners)["ConnectionRefused"].clear
    @client.add_listener("ConnectionRefused") { |msg| @messages << "Connection refused " + Array(msg["errors"]).join(" ") }
    @client.add_listener("RoomInfo") { |msg| @seed_name = msg["seed_name"] }
    @client.add_listener("Connected") { |msg| on_connected(msg) }
    @client.add_listener("ReceivedItems") { |msg| on_items(msg) }
    @client.add_listener("LocationInfo") { |msg| on_scouts(msg) }
    @client.connect
  rescue StandardError => e
    @messages << "Archipelago error " + e.message
  end

  def self.on_connected(msg)
    real = {}
    (msg["missing_locations"] + msg["checked_locations"]).each { |id| real[id] = true }
    @slot = msg["slot"]
    @players = {}
    (msg["players"] || []).each { |p| @players[p["slot"]] = p["alias"] || p["name"] }
    @slot_info = msg["slot_info"] || {}
    slot_data = msg["slot_data"] || {}
    @goal = ENDING_GOALS[slot_data["goal"].to_i]
    mirrors = @mirror_table.select { |m| @key_to_id[m[5]] && real[@key_to_id[m[5]]] }
    BSAP.load_net_session(@seed_name || "net", real, slot_data, @key_to_id, mirrors)
    @connected = true
    @need_sync = true
    @client.locations.scout(0, *real.keys)
    @messages << "Connected to Archipelago as " + @players[@slot].to_s
  rescue StandardError => e
    @messages << "Archipelago error " + e.message
  end

  def self.on_items(msg)
    start = msg["index"].to_i
    @net_items = [] if start == 0
    msg["items"].each_with_index do |item, i|
      row = @item_table[item["item"].to_s]
      sender = @players[item["player"]].to_s
      @net_items[start + i] = row ? [row[0], row[1], row[2], sender] : ["none", 0, 0, sender]
    end
  end

  def self.on_scouts(msg)
    msg["locations"].each do |loc|
      game = (@slot_info[loc["player"].to_s] || {})["game"]
      name = begin
        @client.items.name(game, loc["item"])
      rescue StandardError
        "an item"
      end
      text = loc["player"] == @slot ? "Found your " + name : "Found " + name + " for " + @players[loc["player"]].to_s
      (@id_to_keys[loc["location"]] || []).each { |key| BSAP.set_scout(key, text) }
    end
  end

  def self.send_check(key)
    return unless @connected
    if key.start_with?("ending:")
      @client.update_status(30) if @goal.nil? || key == "ending:" + @goal
      return
    end
    id = @key_to_id[key]
    @client.locations.check(id) if id
  end

  def self.pending_from(start)
    rows = []
    (start...@net_items.length).each do |i|
      row = @net_items[i]
      break if row.nil?
      rows << [i, row[0], row[1], row[2], row[3]]
    end
    rows
  end

  def self.update
    until @messages.empty?
      BSAP.popup(@messages.shift, "Archipelago")
    end
    if @connected && @need_sync && $game_system
      @need_sync = false
      $game_system.bsap_checked.keys.each { |key| send_check(key) }
    end
    if !@connected && @last_attempt && Time.now - @last_attempt > RETRY_SECONDS
      @client.disconnect rescue nil
      connect
    end
  end
end

module BSAP
  def self.load_net_session(seed, real, slot_data, key_to_id, mirrors)
    locs = {}
    bosses = {}
    key_to_id.each do |key, id|
      next unless real[id]
      if key.start_with?("boss:")
        bosses[key[5..-1].to_i] = true
      else
        locs[key] = true
      end
    end
    swaps = {}
    (slot_data["boss_swaps"] || []).each { |s| swaps[s[0].to_i] = [s[1].to_i, s[2].to_f, s[3].to_f] }
    enemy_swaps = {}
    (slot_data["enemy_swaps"] || []).each { |s| enemy_swaps[s[0].to_i] = [s[1].to_i, s[2].to_f, s[3].to_f] }
    mirror_rows = {}
    mirrors.each { |m| (mirror_rows[m[0].to_i] ||= []) << [m[1].to_i, m[2].to_i, m[3].to_i, m[4].to_i, m[5]] }
    @locs = locs
    @boss_checks = bosses
    @swaps = swaps
    @enemy_swaps = enemy_swaps
    @mirrors = mirror_rows
    @scouts ||= {}
    @seed = seed
  end

  def self.set_scout(key, text)
    @scouts[key] = text
  end
end

if BSAPNet.wanted? && BSAPNet.setup
  module BSAP
    class << self
      def refresh_session
      end

      alias bsap_file_check check
      def check(key)
        bsap_file_check(key)
        BSAPNet.send_check(key)
      end

      alias bsap_file_update_map update_map
      def update_map
        BSAPNet.update
        bsap_file_update_map
      end

      def pending_items
        BSAPNet.pending_from($game_system.bsap_received)
      end
    end
  end
  BSAPNet.connect
end
