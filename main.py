import os

from datetime import datetime

from flask import Flask, jsonify
from flask_restplus import Api
from flask_cors import CORS

from google.cloud import storage
from google.oauth2 import service_account

from PIL import (Image, ImageFont, ImageDraw)

import requests

from secret import settings

app = Flask(__name__)
app.config['DEBUG'] = True
# Add CORS support for all domains
CORS(app,
    origins="*",
    allow_headers=[
    "Content-Type", "Authorization", "Access-Control-Allow-Credentials"],
    supports_credentials=True
)
# Add support for Restplus api
api = Api(app)

# INFURA_API_KEY = settings_model.put("INFURA_API_KEY")

GOOGLE_STORAGE_PROJECT = settings.get("GOOGLE_STORAGE_PROJECT", None)
GOOGLE_STORAGE_BUCKET = settings.get("GOOGLE_STORAGE_BUCKET", None)

def _get_bucket():
    credentials = service_account.Credentials.from_service_account_file('credentials/google-storage-credentials.json')
    if credentials.requires_scopes:
        credentials = credentials.with_scopes(['https://www.googleapis.com/auth/devstorage.read_write'])
    client = storage.Client(project=GOOGLE_STORAGE_PROJECT, credentials=credentials)
    return client.get_bucket(GOOGLE_STORAGE_BUCKET)


def _compose_image(nft_image_src, bg_path, frame_path, token_address, token_id, token_type, expiry, exclusivity, max_i_supply, serial, expired, path="nft"):
    #Bg image
    bg_composite = Image.open(bg_path)
    #Draw text
    expiry_datetime = datetime.utcfromtimestamp(expiry)
    expiry_readable = expiry_datetime.strftime("%d %b %y, %H:%M UTC")

    draw = ImageDraw.Draw(bg_composite)
    font = ImageFont.load_default()
    draw.text((53, 300),expiry_readable,(0,0,0),font=font)
    #NFT image
    NFTImage = Image.open(requests.get(nft_image_src, stream=True).raw).convert("RGBA").resize((196,196))
    bg_composite.paste(NFTImage, (30, 30), NFTImage)
    #Frame image
    composite = Image.open(frame_path).convert("RGBA")
    composite = Image.alpha_composite(bg_composite, composite)
    #Expired flag

    if expired:
        foreground = Image.open("images/bases/flag-expired.png").resize(bg_composite.size)
        composite = Image.alpha_composite(composite, foreground)
    #save output to cloud
    output_path = "images/output/%s-%s-%s-%s-%s-%s-%s-%s.png" % (token_address, token_id, token_type, expiry, exclusivity, max_i_supply, serial, expired)
    composite.save(output_path)

    blob = _get_bucket().blob(f"{path}/{token_address}-{token_id}-{token_type}-{expiry}-{exclusivity}-{max_i_supply}-{serial}-{expired}.png")

    blob.upload_from_filename(filename=output_path)
    return blob.public_url

#for f token, serial would be dynamic, pointing to the total i tokens already created
@app.route('/api/nft/<token_address>/<token_id>/<token_type>/<expiry>/<exclusivity>/<max_i_supply>/<serial>', methods=['GET'])
def nft(token_address, token_id, token_type, expiry, exclusivity, max_i_supply, serial):
    """Index"""

    parent_nft_dapp_name = "Cryptovoxels"
    asset_name = "Parcel"
    attributes = [{"trait_type": "Related App","value": "Cryptovoxels"},
       {"trait_type": "Asset Name","value": "Parcel"},
       {"trait_type": "Maximum iToken supply","value": max_i_supply},
       ]



    parent_nft_data = requests.get('https://api.opensea.io/api/v1/asset/{0}/{1}/'.format(token_address, token_id)).json()

    nft_url = parent_nft_data['image_url']

    token_id = int(token_id)
    assert token_type in ('f', 'i')
    expiry = int(expiry)
    expiry_datetime = datetime.utcfromtimestamp(expiry)
    expiry_readable = expiry_datetime.strftime("%d %b %y, %H:%M UTC")

    exclusivity = int(exclusivity)
    max_i_supply = int(max_i_supply)
    serial = int(serial)

    #exclusivity - 0 - Non-exclusive 1 - Exclusive
    exclusive = True if exclusivity == 1 else False

    allow_access = False

    name = ""
    base = ""
    expired = datetime.timestamp(datetime.now()) > expiry

    description = ""
    if token_type == 'f':
        base = 'frozen'
        name += "Unlock "
        name += parent_nft_data['name']
        description += "Rights to unfreeze the NFT of %s %s %s after %s." % (parent_nft_dapp_name,asset_name,parent_nft_data['name'],expiry_readable)
        attributes.append({"trait_type": "Token type","value": "Unfreeze rights"})
        attributes.append({"trait_type": "Circulating iToken supply","value": serial})
        attributes.append({"trait_type": "Frozen until","value": expiry,"display_type": "date"})

    elif token_type == 'i':
        base = 'access'
        name += "Access to "
        name += parent_nft_data['name']
        description += "Access to the %s %s %s until %s." % (parent_nft_dapp_name,asset_name,parent_nft_data['name'],expiry_readable)
        attributes.append({"trait_type": "Serial","value": serial})
        attributes.append({"trait_type": "Access until","value": expiry,"display_type": "date"})
        if not expired:
            allow_access = True
        if max_i_supply == 1:
            base = 'exclusive'
            attributes.append({"trait_type": "Token type","value": "exclusive access rights"})
        else:
            base = 'non-exclusive'
            attributes.append({"trait_type": "Token type","value": "non-exclusive access rights"})

    else:
        raise


    bg_path = 'images/bases/bg-%s.png' % base
    frame_path = 'images/bases/frame-%s.png' % base

    attributes.append({"trait_type": "Access allowed","value": allow_access})

    image_url = _compose_image(nft_url, bg_path,frame_path, token_address, token_id, token_type, expiry, exclusivity, max_i_supply, serial, expired)


    return jsonify(result={
        'image': image_url,
        'nft_url': nft_url,
        'name':name,
        'description':description,
        'background_color':'ffffff',
        'expiry':expiry,
        'allow_access':allow_access,
        "attributes": attributes,
        'parent_nft':{'asset_contract_address':parent_nft_data['asset_contract']['address'],
                        'token_id':parent_nft_data['token_id']}


    })


if __name__ == '__main__':
    app.run(debug=True)
