"""Verified owner-provided illustration inputs. No synthesis, network or publication."""
from pathlib import Path
import hashlib,re
from PIL import Image

def validate_asset(asset, root):
    if asset.get('asset_type') != 'illustration':
        raise ValueError('Illustration asset type required')
    if asset.get('contains_text') is not False:
        raise ValueError('Supply background artwork only; renderer owns typography')
    for key in ('scene','scene_match','creator','rights_evidence','origin_reference'):
        if not isinstance(asset.get(key),str) or not asset[key].strip():
            raise ValueError('Missing illustration provenance: '+key)
    if asset.get('rights_confirmed') is not True or asset.get('illustrative_not_real_event') is not True:
        raise ValueError('Illustration rights and non-event disclosure required')
    relative=Path(asset.get('asset_path',''))
    root=Path(root).resolve()
    target=(root/relative).resolve()
    if relative.is_absolute() or not target.is_relative_to(root/'assets'/'editorial') or not target.is_file():
        raise ValueError('Illustration must be an existing repository editorial asset')
    digest=asset.get('sha256','')
    if not re.fullmatch('[a-f0-9]{64}',digest) or hashlib.sha256(target.read_bytes()).hexdigest()!=digest:
        raise ValueError('Illustration immutable hash mismatch')
    with Image.open(target) as im:
        im.load()
        if im.width<1080 or im.height<1920:
            raise ValueError('Illustration below original 1080x1920; refusing upscale')
    return target

def select_illustration(asset, placements, query, guard, used, root):
    from photo_preflight import readable_crop
    target=validate_asset(asset,root)
    identity=asset['sha256']
    if identity in used: raise ValueError('Repeated illustration')
    class IllustrationGuard:
        def approved(self,image,scene):
            return guard.approved(image,scene,visual_kind='illustration')
    with Image.open(target) as im:
        crop,placement,center=readable_crop(im.convert('RGB'),placements,query,IllustrationGuard())
    used.add(identity)
    source='illustration-sha256:'+identity
    evidence={'asset_type':'illustration','source':source,'asset_sha256':identity,
              'origin_reference':asset['origin_reference'],'rights_evidence':asset['rights_evidence'],
              'crop_center':center,'visual_semantic_qa':True,'photo_semantic_qa':False}
    return crop,placement,dict(asset,source=source),evidence

def validate_visual_evidence(info):
    if info.get('asset_type','photograph')=='illustration':
        if (info.get('photo_semantic_qa') is not False or info.get('visual_semantic_qa') is not True
                or not re.fullmatch('illustration-sha256:[a-f0-9]{64}',info.get('source',''))
                or not info.get('rights_evidence') or not info.get('origin_reference')):
            raise ValueError('Illustration evidence incomplete; never impersonate photo QA')
    elif info.get('photo_semantic_qa') is not True:
        raise ValueError('Photographic semantic evidence missing')
