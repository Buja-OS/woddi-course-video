set -x
cd out
curl -sS "https://api.polyhaven.com/assets?t=models" -o ph_models.json
curl -sS "https://api.polyhaven.com/assets?t=hdris&c=indoor" -o ph_hdris.json
for m in yor hau ibo swh ara arb fra por eng; do code=$(curl -s -o /dev/null -w "%{http_code}" -L https://huggingface.co/facebook/mms-tts-$m/resolve/main/config.json); echo "mms-$m $code"; done > mms.txt
UA="WODDI-Institute-video-bot/1.0 (noreply@woddiinstitute.com)"
for q in "sodium hydroxide" "caustic soda" "soap making" "lye soap" "palm oil" "palm kernel oil" "coconut oil" "shea butter" "handmade soap" "liquid soap" "soap mould" "pH test strip" "nitrile gloves" "safety goggles" "digital kitchen scale" "plastic bucket" "glycerin" "shampoo" "dish soap" "bleach" "laundry soap Africa" "Nigeria market"; do
  curl -sS -A "$UA" "https://commons.wikimedia.org/w/api.php?action=query&generator=search&gsrsearch=$(python3 -c "import urllib.parse,sys;print(urllib.parse.quote(sys.argv[1]+' filetype:bitmap'))" "$q")&gsrnamespace=6&gsrlimit=25&prop=imageinfo&iiprop=url|size|extmetadata&iiurlwidth=1280&format=json" -o "wm_$(echo $q|tr ' ' _).json"
done
ls -la
