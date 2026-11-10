# Checklist screen in the pause menu, BSAP_CHECKLIST rows are [keys, area, name] and come from the client

module BSAP
  def self.row_real?(row)
    row[0].any? { |k| k.start_with?("boss:") ? boss_check?(k[5..-1].to_i) : loc?(k) }
  end

  def self.row_done?(row)
    row[0].any? { |k| done?(k) }
  end

  PRINCESS_ROOM_AREAS = ["Tainted Bog", "Gothel's Tower", "Garden of Snow", "Atlantica"]

  # a princess takes her checks with her to the room she was moved to
  def self.row_area(row)
    r = defined?(Rando) && Rando.data
    return row[1] unless r && r[:rooms]
    key = row[0][0]
    RandoData::PRINCESSES.each_with_index do |p, i|
      home = key.start_with?("boss:") ? key == "boss:#{p[:troop]}" : key.start_with?("#{p[:map]}:#{p[:ev]}:")
      return PRINCESS_ROOM_AREAS[r[:rooms].index(i)] if home
    end
    row[1]
  end

  # areas in route order, each with its rows still to do first
  def self.checklist_areas
    return [] unless active? && defined?(BSAP_CHECKLIST)
    order = []
    by_area = {}
    BSAP_CHECKLIST.each do |row|
      next unless row_real?(row)
      area = row_area(row)
      unless by_area[area]
        by_area[area] = []
        order << area
      end
      by_area[area] << row
    end
    order.map { |a| [a, by_area[a]] }
  end
end

class Window_BSAPAreas < Window_Command
  def initialize(y, areas)
    @areas = areas
    @window_h = Graphics.height - y
    super(0, y)
  end

  def window_width
    240
  end

  def window_height
    @window_h
  end

  def make_command_list
    @areas.each { |a| add_command(a[0], :area) }
  end

  def draw_item(index)
    rows = @areas[index][1]
    done = rows.count { |r| BSAP.row_done?(r) }
    rect = item_rect_for_text(index)
    change_color(normal_color, done < rows.size)
    draw_text(rect.x, rect.y, rect.width - 60, rect.height, @areas[index][0])
    draw_text(rect.x, rect.y, rect.width, rect.height, "#{done}/#{rows.size}", 2)
  end
end

class Window_BSAPChecks < Window_Selectable
  def initialize(x, y, w, h)
    @rows = []
    super(x, y, w, h)
    refresh
  end

  def rows=(rows)
    @rows = rows.select { |r| !BSAP.row_done?(r) } + rows.select { |r| BSAP.row_done?(r) }
    self.oy = 0
    refresh
  end

  def item_max
    @rows.size
  end

  def draw_item(index)
    row = @rows[index]
    done = BSAP.row_done?(row)
    rect = item_rect_for_text(index)
    change_color(normal_color, !done)
    draw_text(rect.x, rect.y, 24, rect.height, done ? "■" : "□")
    draw_text(rect.x + 28, rect.y, rect.width - 28, rect.height, row[2])
  end
end

class Scene_BSAPChecklist < Scene_MenuBase
  def start
    super
    @areas = BSAP.checklist_areas
    @head = Window_Help.new(1)
    @head.viewport = @viewport
    @area_window = Window_BSAPAreas.new(@head.height, @areas)
    @area_window.viewport = @viewport
    @area_window.set_handler(:area, method(:on_area))
    @area_window.set_handler(:cancel, method(:return_scene))
    x = @area_window.width
    @check_window = Window_BSAPChecks.new(x, @head.height, Graphics.width - x, Graphics.height - @head.height)
    @check_window.viewport = @viewport
    @check_window.set_handler(:cancel, method(:on_back))
    all = @areas.flat_map { |a| a[1] }
    if all.empty?
      @head.set_text("Not connected to Archipelago yet")
    else
      @head.set_text("Checks done  #{all.count { |r| BSAP.row_done?(r) }} / #{all.size}")
    end
    @shown = nil
    show_area
  end

  def update
    super
    show_area if @area_window.active
  end

  def show_area
    i = @area_window.index
    return if i == @shown
    @shown = i
    @check_window.rows = i >= 0 && @areas[i] ? @areas[i][1] : []
  end

  def on_area
    return @area_window.activate if @check_window.item_max == 0
    @check_window.select(0)
    @check_window.activate
  end

  def on_back
    @check_window.unselect
    @check_window.oy = 0
    @area_window.activate
  end
end

class Window_MenuCommand
  alias bsap_add_original_commands add_original_commands unless method_defined?(:bsap_add_original_commands)
  def add_original_commands
    bsap_add_original_commands
    add_command("Checklist", :bsap_checklist) if BSAP.active? && BSAP.opt("pause_menu_checklist") != "false"
  end
end

class Scene_Menu
  alias bsap_create_command_window create_command_window unless method_defined?(:bsap_create_command_window)
  def create_command_window
    bsap_create_command_window
    @command_window.set_handler(:bsap_checklist, method(:command_bsap_checklist))
  end

  def command_bsap_checklist
    SceneManager.call(Scene_BSAPChecklist)
  end
end
