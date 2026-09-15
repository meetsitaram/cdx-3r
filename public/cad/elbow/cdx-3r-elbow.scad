// CDX-3R elbow — mm
// part: assembly | fork_l | fork_r | hub | drum | cuff_forearm | cuff_upper | bowden | stop
part = "assembly";

upper_arm_len   = 290;
forearm_len     = 260;
tube_od         = 25;
sheave_od       = 88.9;
sheave_pitch    = 76.2;
sheave_w        = 17.46;
sheave_bore     = 19.05;
shaft_d         = 19.05;
fork_t          = 8;
fork_span       = sheave_w + 14;
cuff_id_fa      = 95;
cuff_id_ua      = 105;
cuff_t          = 8;
insert_m4       = 4.6;

$fn = 48;

module tube(len) {
  difference() {
    cylinder(h=len, d=tube_od, center=true);
    cylinder(h=len+1, d=tube_od-2.4, center=true);
  }
}

module cot_sheave() {
  color("gold") difference() {
    union() {
      cylinder(h=sheave_w, d=sheave_od, center=true);
    }
    cylinder(h=sheave_w+1, d=sheave_bore, center=true);
    rotate_extrude() translate([sheave_pitch/2, 0, 0]) circle(d=6);
  }
}

module print_drum() {
  difference() {
    union() {
      cylinder(h=sheave_w, d=sheave_od-4, center=true);
      translate([0,0, sheave_w/2-2]) cylinder(h=4, d=sheave_od-2, center=true);
      translate([0,0,-sheave_w/2+2]) cylinder(h=4, d=sheave_od-2, center=true);
    }
    cylinder(h=sheave_w+2, d=shaft_d+0.3, center=true);
    rotate_extrude() translate([sheave_pitch/2, 0, 0]) circle(d=5.5);
  }
}

module fork(mirror_z=1) {
  w = 78; h = 58;
  difference() {
    hull() {
      translate([0,0,0]) cylinder(h=fork_t, d=36, center=true);
      translate([-32,0,0]) cube([24, 34, fork_t], center=true);
    }
    cylinder(h=fork_t+1, d=shaft_d+0.3, center=true);
    // 25 mm tube saddle
    translate([-30,0,0]) rotate([0,90,0]) cylinder(h=40, d=tube_od+0.4, center=true);
    // M4 inserts
    for (y=[-12,12]) translate([-38,y,0])
      cylinder(h=fork_t+1, d=insert_m4, center=true);
  }
}

module forearm_hub() {
  difference() {
    union() {
      cylinder(h=12, d=44, center=true);
      translate([28,0,0]) cube([40, 34, 12], center=true);
    }
    cylinder(h=14, d=shaft_d+0.3, center=true);
    translate([30,0,0]) rotate([0,90,0]) cylinder(h=50, d=tube_od+0.4, center=true);
    for (a=[0,90,180,270]) rotate([0,0,a])
      translate([16,0,0]) cylinder(h=14, d=insert_m4, center=true);
  }
}

module cuff(id) {
  od = id + 2*cuff_t;
  difference() {
    cylinder(h=48, d=od, center=true);
    cylinder(h=50, d=id, center=true);
    translate([od/2,0,0]) cube([od, 28, 52], center=true);
  }
  for (z=[-16,16]) for (s=[-1,1])
    translate([s*(id/2+cuff_t+6), 0, z]) difference() {
      cube([14, 10, 8], center=true);
      rotate([90,0,0]) cylinder(h=12, d=6, center=true);
    }
}

module bowden_anchor() {
  difference() {
    cube([28, 18, 16], center=true);
    translate([0,0,0]) rotate([0,90,0]) cylinder(h=30, d=5.3, center=true);
    translate([-8,0,0]) rotate([0,90,0]) cylinder(h=8, d=7.2, center=true); // ferrule
    translate([0,0,0]) cylinder(h=18, d=3.3, center=true); // M3 clamp
  }
}

module hard_stop() {
  difference() {
    cube([30, 18, 14], center=true);
    translate([-8,0,0]) rotate([90,0,0]) cylinder(h=20, d=shaft_d+0.4, center=true);
  }
}

module assembly() {
  color("seagreen") {
    translate([0,0, fork_span/2]) fork();
    translate([0,0,-fork_span/2]) fork();
  }
  cot_sheave();
  color("gray") cylinder(h=100, d=shaft_d, center=true);
  color("silver") {
    translate([-80,0,0]) rotate([0,90,0]) tube(160);
    rotate([90,0,0]) translate([0,0,-80]) tube(160);
  }
  color("seagreen") {
    translate([0, 55, 0]) rotate([90,0,0]) cuff(cuff_id_fa);
    translate([-90,0,0]) rotate([0,90,0]) cuff(cuff_id_ua);
    translate([-40, 28,  20]) bowden_anchor();
    translate([-40, 28, -20]) bowden_anchor();
    translate([18, -28, 0]) hard_stop();
  }
}

if (part=="fork_l") fork();
else if (part=="fork_r") fork();
else if (part=="hub") forearm_hub();
else if (part=="drum") print_drum();
else if (part=="cuff_forearm") cuff(cuff_id_fa);
else if (part=="cuff_upper") cuff(cuff_id_ua);
else if (part=="bowden") bowden_anchor();
else if (part=="stop") hard_stop();
else assembly();
