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


def _compose_expiry(composite, expiry, expired):
    img = Image.open("sample_in.jpg")
    draw = ImageDraw.Draw(img)
    # font = ImageFont.truetype(<font-file>, <font-size>)
    font = ImageFont.truetype("sans-serif.ttf", 16)
    # draw.text((x, y),"Sample Text",(r,g,b))
    draw.text((0, 0),"Expires on {0}".format(datetime.fromtimestamp(expiry).isoformat()),(255,255,255),font=font)
    img.save('sample-out.jpg')


def _compose_image(nft_image_src, image_files, token_address, token_id, token_type, expiry, max_i_supply, expired, path="nft"):
    base_composite = Image.open("images/bases/base-exclusive.png").convert("RGBA")
    composite = Image.open(requests.get(nft_image_src, stream=True).raw).convert("RGBA").resize(base_composite.size)
    for image_file in image_files:
        foreground = Image.open(image_file).convert("RGBA").resize(base_composite.size)
        composite = Image.alpha_composite(composite, foreground)

    if expired:
        foreground = Image.open("images/bases/base-expired.png").resize(base_composite.size)
        composite = Image.alpha_composite(composite, foreground)

    output_path = "images/output/%s-%s-%s-%s-%s.png" % (token_address, token_id, token_type, expiry, max_i_supply)
    composite.save(output_path)

    blob = _get_bucket().blob(f"{path}/{token_address}-{token_id}-{token_type}-{expiry}-{max_i_supply}.png")
    blob.upload_from_filename(filename=output_path)
    return blob.public_url


@app.route('/api/nft/<token_address>/<token_id>/<token_type>/<expiry>/<max_i_supply>', methods=['GET'])
def nft(token_address, token_id, token_type, expiry, max_i_supply):
    """Index"""

    nft_url = requests.get('https://api.opensea.io/api/v1/asset/{0}/{1}/'.format(token_address, token_id)).json()['image_url']
    token_id = int(token_id)
    assert token_type in ('f', 'i')
    expiry = int(expiry)
    max_i_supply = int(max_i_supply)
    exclusive = True if max_i_supply == 1 else False
    if token_type == 'f':
        base = 'frozen'
    elif max_i_supply == 1:
        base = 'exclusive'
    else:
        base = 'non-exclusive'
    base_path = 'images/bases/base-%s.png' % base
    expired = datetime.timestamp(datetime.now()) > expiry
    image_url = _compose_image(nft_url, [base_path],
                              token_address, token_id, token_type, expiry, max_i_supply, expired)
    return jsonify(result={
        'image': image_url,
        'nft_url': nft_url
    })


if __name__ == '__main__':
    app.run(debug=True)
