#!/usr/bin/env python3
"""Regenerate CAD proof views and portal previews from synchronized STL files."""
from pathlib import Path
import json
import shutil
from render_mesh import render, system_names, arm_names, PUBLIC
CAD=Path(__file__).resolve().parent


def save(kit,names,filename,source=None,view=(.45,.28,1),size=(1200,1100)):
    path=PUBLIC/kit/'preview'/filename
    render(source or kit,names,path,view,size)
    local=CAD/kit/'preview'/filename;local.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(path,local)


PARTS={
    'elbow': {'fork':'print_fork_lateral','cuff':'print_cuff_forearm','hub':'print_forearm_hub',
        'drum':'print_drum','anchor':'print_bowden_anchor','stop':'print_hard_stop',
        'sheave':'ref_sheave_DO_NOT_PRINT','bearing':'ref_608_DO_NOT_PRINT','screw':'ref_shoulder_screw_DO_NOT_PRINT','arm':'ref_arm_ghost_DO_NOT_PRINT'},
    'shoulder': {'scapula':'print_scapula','flex':'print_flex_yoke','abd':'print_abd_yoke','cuff':'print_deltoid_cuff','comb':'print_cable_comb'},
    'backpack': {'frame':'print_frame','sled':'print_sled','battery':'ref_battery_DO_NOT_PRINT','motor':'ref_motor_DO_NOT_PRINT',
        'gear':'ref_planetary_DO_NOT_PRINT','s1':'ref_s1_DO_NOT_PRINT','drum':'print_drum','bulkhead':'print_bulkhead'},
    'system': {'saddle':'print_saddle','yoke':'print_yoke','beam':'print_ua_beam','belt':'print_hip_belt','park':'print_park_rest'},
}


def parts_main(kits=tuple(PARTS)):
    for kit in kits:
        for file,part in PARTS.get(kit,{}).items():save(kit,[part],file+'.png',size=(700,600))


def main(kits=('armor','system','backpack','shoulder','elbow')):
    if 'armor' in kits:
        save('armor',arm_names(),'worn.png',source='system')
        save('armor',[n for n in arm_names() if n.startswith('sh_') or n in ['ar_deltoid','ar_deltoid_front','ar_deltoid_rear','ar_bezel','ar_shoulder_trim']],'joint.png',source='system',size=(1000,900))
        for file,part in [('ua','ua'),('fa','fa'),('deltoid','deltoid'),('scapula','scapula'),('pack','pack_tub'),('lid','pack_lid')]:
            save('armor',[f'print_fairing_{part}'],file+'.png',size=(700,600))
    if 'system' in kits:
        save('system',system_names(),'worn.png',view=(-.62,.24,1),size=(1500,1400))
        save('system',[n for n in system_names() if n!='human' and not n.startswith('ghost_')],'worn_gear.png',view=(-.62,.24,1),size=(1500,1400))
        save('system',arm_names(),'arm.png',view=(.55,.38,1),size=(1400,1300))
        render('system',arm_names(),CAD/'system/preview/arm-clay.png',view=(.55,.38,1),size=(1400,1300),clay=True)
        save('system',['human','ghost_upper','ghost_forearm','saddle','yoke','beam','belt','park','pk_frame'],'loadpath.png',view=(-.62,.24,1))
    if 'backpack' in kits:
        names=list(json.loads((PUBLIC/'backpack/asm/colors.json').read_text())['layers'])
        save('backpack',[n for n in names if n not in ['torso','strap']],'assembly.png',view=(.55,.25,1))
        save('backpack',names,'worn.png',view=(.55,.25,1))
    for kit in ['elbow','shoulder']:
        if kit not in kits:continue
        manifest=json.loads((PUBLIC/kit/'asm/colors.json').read_text())
        save(kit,manifest['views']['worn'],'worn.png')
        save(kit,manifest['views']['brace'],'assembly.png')

    parts_main(kits)


if __name__=='__main__':
    import sys
    main(tuple(sys.argv[1:]) or ('armor','system','backpack','shoulder','elbow'))
