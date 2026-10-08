set -x
OUT=$PWD/out; mkdir -p $OUT/ph && cd $OUT/ph
for m in yellow_onion food_apple_01 food_avocado_01 food_lime_01 lemon sweet_potato bananas croissant hamburger_buns carrot_cake strawberry_chocolate_cake food_ginger_01 watering_can_metal_01 medical_box vintage_flashlight alarm_clock_01 magnifying_glass_01 cardboard_box_01 wicker_basket_01 wicker_basket_02 potted_plant_01 potted_plant_02 planter_box_01 seeding_tray_01 compost_bag_02 trowel_01 brass_candleholders ceramic_vase_01 ceramic_vase_03 throw_pillows_01 wooden_crate_01 wooden_crate_02 standing_chalkboard_01 round_wooden_table_01 outdoor_table_chair_set_01 modern_coffee_table_01 tool_cart metal_office_desk wooden_bowl_02 brass_pot_01 pot_enamel_01 plastic_crate_02 plastic_crate_03 long_life_food russian_food_cans_01 wooden_picnic_table portable_cassette_player pastic_torch_6v sungka_board wooden_candlestick vintage_oil_lamp spray_paint_bottles planter_pot_clay potted_plant_04 wooden_bookshelf_worn decorative_book_set_01 standing_picture_frame_01 ceramic_vase_02 brass_vase_01 painted_wooden_table industrial_pastic_container plastic_container modified_thermos vintage_suitcase; do
  curl -sS "https://api.polyhaven.com/files/$m" -o files.json
  python3 - "$m" <<'P'
import json,sys,os,urllib.request
m=sys.argv[1]
try: d=json.load(open('files.json'))
except Exception: print('bad',m); sys.exit()
g=d.get('gltf',{}).get('1k',{}).get('gltf')
if not g: print('NO GLTF',m); sys.exit()
os.makedirs(m,exist_ok=True)
def get(u,p):
    os.makedirs(os.path.dirname(p) or '.',exist_ok=True); urllib.request.urlretrieve(u,p)
get(g['url'],m+'/'+m+'.gltf')
for rel,inc in g.get('include',{}).items(): get(inc['url'],m+'/'+rel)
print('ok',m)
P
done
rm -f files.json
mkdir -p hdri && for h in kitchen_2 bush_restaurant cayley_interior small_empty_room_3 photo_studio_loft_hall studio_small_08 rural_asphalt_road; do curl -sSfL "https://dl.polyhaven.org/file/ph-assets/HDRIs/hdr/2k/${h}_2k.hdr" -o hdri/$h.hdr || echo "nohdri $h"; done
mkdir -p tex; for t in fabric_pattern_05 fabric_pattern_07 denim_fabric cotton_jersey brown_mud_leaves_01 rocky_trail aerial_rocks_02 burlap wood_floor_deck painted_plaster_wall concrete_floor_02 gray_rocks forest_ground_04 red_brick_03 leather_red_02 knitted_fleece; do mkdir -p tex/$t; for k in diff_2k.jpg nor_gl_2k.jpg rough_2k.jpg; do curl -sSfL "https://dl.polyhaven.org/file/ph-assets/Textures/jpg/2k/$t/${t}_$k" -o tex/$t/${t}_$k || rm -f tex/$t/${t}_$k; done; done
du -sh $OUT/ph
