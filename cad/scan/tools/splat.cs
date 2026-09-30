// Minimal SPZ v2/v3 decoder + orthographic point renderer (no Python needed).
// Build: csc /O /out:splat.exe splat.cs /r:System.Drawing.dll
//   splat decode <in.spz.raw> <out.pts>        -> float32 records x y z r g b a s
//   splat stats  <pts> [box]
//   splat render <pts> <view> <px_per_m> <out.png> [box] [amin]
//        view: front|back|left|right|top|bottom ; box = x0 x1 y0 y1 z0 z1
//   splat ply    <pts> <out.ply> [box] [amin]   -> ascii ply (x y z r g b)
using System; using System.IO; using System.Drawing; using System.Drawing.Imaging;
using System.Collections.Generic; using System.Globalization;

class P {
  static CultureInfo C = CultureInfo.InvariantCulture;
  static float F(string s){ return float.Parse(s, C); }
  static float[] Load(string f){
    byte[] b = File.ReadAllBytes(f); float[] a = new float[b.Length/4];
    Buffer.BlockCopy(b,0,a,0,b.Length); return a; }
  static float[] Box(string[] a, int i){
    if (a.Length < i+6) return new float[]{-1e9f,1e9f,-1e9f,1e9f,-1e9f,1e9f};
    float[] r = new float[6]; for(int k=0;k<6;k++) r[k]=F(a[i+k]); return r; }
  static bool In(float[] p, int o, float[] bx){
    return p[o]>=bx[0]&&p[o]<=bx[1]&&p[o+1]>=bx[2]&&p[o+1]<=bx[3]&&p[o+2]>=bx[4]&&p[o+2]<=bx[5]; }
  const int R = 8;

  static void Main(string[] a){
    if (a[0]=="decode") Decode(a[1], a[2]);
    else if (a[0]=="stats") Stats(Load(a[1]), Box(a,2));
    else if (a[0]=="render") Render(Load(a[1]), a[2], F(a[3]), a[4], Box(a,5), a.Length>11?F(a[11]):0.3f);
    else if (a[0]=="ply") Ply(Load(a[1]), a[2], Box(a,3), a.Length>9?F(a[9]):0.3f);
  }

  static void Decode(string inf, string outf){
    byte[] d = File.ReadAllBytes(inf);
    int ver = BitConverter.ToInt32(d,4), n = BitConverter.ToInt32(d,8);
    int fb = d[13]; float sc = 1f/(1<<fb);
    int pos=16, alp=pos+9*n, col=alp+n, scl=col+3*n;
    float[] o = new float[n*R];
    for (int i=0;i<n;i++){
      for (int k=0;k<3;k++){
        int q = pos+9*i+3*k; int v = d[q] | (d[q+1]<<8) | (d[q+2]<<16);
        if ((v & 0x800000)!=0) v |= unchecked((int)0xFF000000);
        o[i*R+k] = v*sc; }
      for (int k=0;k<3;k++){
        float dc = (d[col+3*i+k]/255f - 0.5f)/0.15f;
        o[i*R+3+k] = Math.Max(0f, Math.Min(1f, 0.5f + 0.282095f*dc)); }
      o[i*R+6] = d[alp+i]/255f;
      float m = 0; for(int k=0;k<3;k++) m = Math.Max(m, d[scl+3*i+k]/16f - 10f);
      o[i*R+7] = (float)Math.Exp(m);
    }
    byte[] b = new byte[o.Length*4]; Buffer.BlockCopy(o,0,b,0,b.Length); File.WriteAllBytes(outf,b);
    Console.WriteLine("version {0}, {1} splats, fracbits {2}", ver, n, fb);
  }

  static void Stats(float[] p, float[] bx){
    int n = p.Length/R; var ax = new List<float>[3]; for(int k=0;k<3;k++) ax[k]=new List<float>();
    int cnt=0;
    for(int i=0;i<n;i++){ if(!In(p,i*R,bx) || p[i*R+6]<0.3f) continue; cnt++;
      for(int k=0;k<3;k++) ax[k].Add(p[i*R+k]); }
    Console.WriteLine("{0} splats (alpha>=0.3) in box", cnt);
    string[] nm={"x","y","z"};
    for(int k=0;k<3;k++){ ax[k].Sort(); var L=ax[k]; if(L.Count==0) continue;
      Console.Write(nm[k]+":");
      foreach(double q in new double[]{0,0.01,0.05,0.25,0.5,0.75,0.95,0.99,1})
        Console.Write(" {0:F3}", L[(int)Math.Min(L.Count-1, q*L.Count)]);
      Console.WriteLine(); }
  }

  // view -> (u axis, u sign, v axis, v sign, depth axis, depth sign toward viewer)
  static int[] View(string v){
    switch(v){
      case "front":  return new[]{0, 1, 1, 1, 2, 1};
      case "back":   return new[]{0,-1, 1, 1, 2,-1};
      case "right":  return new[]{2,-1, 1, 1, 0, 1};
      case "left":   return new[]{2, 1, 1, 1, 0,-1};
      case "top":    return new[]{0, 1, 2,-1, 1, 1};
      default:       return new[]{0, 1, 2, 1, 1,-1}; }
  }

  static void Render(float[] p, string view, float ppm, string outf, float[] bx, float amin){
    int n = p.Length/R; int[] V = View(view);
    float u0=1e9f,u1=-1e9f,v0=1e9f,v1=-1e9f;
    for(int i=0;i<n;i++){ int o=i*R; if(!In(p,o,bx)||p[o+6]<amin) continue;
      float u=p[o+V[0]]*V[1], v=p[o+V[2]]*V[3];
      u0=Math.Min(u0,u);u1=Math.Max(u1,u);v0=Math.Min(v0,v);v1=Math.Max(v1,v); }
    int W=(int)((u1-u0)*ppm)+1, H=(int)((v1-v0)*ppm)+1;
    W=Math.Min(W,4000); H=Math.Min(H,4000);
    float[] z = new float[W*H]; for(int i=0;i<z.Length;i++) z[i]=-1e9f;
    int[] c = new int[W*H];
    for(int i=0;i<n;i++){ int o=i*R; if(!In(p,o,bx)||p[o+6]<amin) continue;
      int x=(int)((p[o+V[0]]*V[1]-u0)*ppm), y=H-1-(int)((p[o+V[2]]*V[3]-v0)*ppm);
      float dz=p[o+V[4]]*V[5];
      int rad = Math.Max(0, Math.Min(3, (int)(p[o+7]*ppm*0.5f)));
      for(int yy=y-rad;yy<=y+rad;yy++) for(int xx=x-rad;xx<=x+rad;xx++){
        if(xx<0||yy<0||xx>=W||yy>=H) continue; int q=yy*W+xx;
        if(dz>z[q]){ z[q]=dz; c[q]=(255<<24)|((int)(p[o+3]*255)<<16)|((int)(p[o+4]*255)<<8)|(int)(p[o+5]*255); } } }
    var bmp = new Bitmap(W,H,PixelFormat.Format32bppArgb);
    for(int y=0;y<H;y++) for(int x=0;x<W;x++){ int q=y*W+x; bmp.SetPixel(x,y, Color.FromArgb(c[q]==0? unchecked((int)0xFF202020):c[q])); }
    // 10 cm grid ticks on the border
    using(var g=Graphics.FromImage(bmp)){ var pen=new Pen(Color.Yellow);
      for(double t=Math.Ceiling(u0*10)/10; t<=u1; t+=0.1){ int x=(int)((t-u0)*ppm); g.DrawLine(pen,x,0,x,(Math.Abs(t-Math.Round(t))<1e-3)?20:8); }
      for(double t=Math.Ceiling(v0*10)/10; t<=v1; t+=0.1){ int y=H-1-(int)((t-v0)*ppm); g.DrawLine(pen,0,y,(Math.Abs(t-Math.Round(t))<1e-3)?20:8,y); } }
    bmp.Save(outf, ImageFormat.Png);
    Console.WriteLine("{0}x{1} px; u [{2:F2},{3:F2}] v [{4:F2},{5:F2}] (signed view coords)", W,H,u0,u1,v0,v1);
  }

  static void Ply(float[] p, string outf, float[] bx, float amin){
    int n=p.Length/R; var sb=new List<string>();
    for(int i=0;i<n;i++){ int o=i*R; if(!In(p,o,bx)||p[o+6]<amin) continue;
      sb.Add(string.Format(C,"{0:F4} {1:F4} {2:F4} {3} {4} {5}",p[o],p[o+1],p[o+2],(int)(p[o+3]*255),(int)(p[o+4]*255),(int)(p[o+5]*255))); }
    using(var w=new StreamWriter(outf)){ w.WriteLine("ply\nformat ascii 1.0\nelement vertex "+sb.Count+
      "\nproperty float x\nproperty float y\nproperty float z\nproperty uchar red\nproperty uchar green\nproperty uchar blue\nend_header");
      foreach(var s in sb) w.WriteLine(s); }
    Console.WriteLine("{0} points -> {1}", sb.Count, outf);
  }
}
