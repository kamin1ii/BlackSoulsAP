Tracker:AddItems("items/items.json")
Tracker:AddMaps("maps/maps.json")
Tracker:AddLocations("locations/locations.json")
Tracker:AddLayouts("layouts/tracker.json")

ScriptHost:LoadScript("scripts/mapping.lua")

CUR_INDEX = -1

function OnClear(slot_data)
    CUR_INDEX = -1
    for _, code in pairs(LOCATION_MAPPING) do
        local section = Tracker:FindObjectForCode(code)
        if section then
            section.AvailableChestCount = section.ChestCount
        end
    end
    for _, code in pairs(ITEM_MAPPING) do
        local item = Tracker:FindObjectForCode(code)
        if item then
            item.Active = false
        end
    end
end

function OnItem(index, item_id, item_name, player_number)
    if index <= CUR_INDEX then
        return
    end
    CUR_INDEX = index
    local code = ITEM_MAPPING[item_id]
    local item = code and Tracker:FindObjectForCode(code)
    if item then
        item.Active = true
    end
end

function OnLocation(location_id, location_name)
    local code = LOCATION_MAPPING[location_id]
    local section = code and Tracker:FindObjectForCode(code)
    if section and section.AvailableChestCount > 0 then
        section.AvailableChestCount = section.AvailableChestCount - 1
    end
end

if Archipelago then
    Archipelago:AddClearHandler("clear handler", OnClear)
    Archipelago:AddItemHandler("item handler", OnItem)
    Archipelago:AddLocationHandler("location handler", OnLocation)
end
