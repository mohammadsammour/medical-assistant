import { Link } from 'react-router-dom';
import { Phone, HeartPulse, ShieldAlert } from 'lucide-react';

export default function Footer() {
  const year = new Date().getFullYear();

  return (
    <footer className="bg-navy text-white/70 mt-auto">
      <div className="max-w-6xl mx-auto px-4 py-10">
        <div className="grid gap-8 sm:grid-cols-3">
          <div>
            <div className="flex items-center gap-2.5 mb-3">
              <span className="grid place-items-center w-9 h-9 rounded-xl gradient-primary shadow-glow">
                <HeartPulse size={18} className="text-white" />
              </span>
              <span className="text-lg font-bold text-white">ميديك زيرو</span>
            </div>
            <p className="text-sm text-white/55 leading-relaxed max-w-xs">
              تقييم مبدئي فوري للإسعافات الأولية بالذكاء الاصطناعي — بلغتك وفي أي لحظة.
            </p>
          </div>

          <div>
            <h4 className="text-white font-semibold text-sm mb-3">روابط سريعة</h4>
            <ul className="space-y-2 text-sm">
              <li><Link to="/assess/new" className="text-white/60 hover:text-white transition">تقييم جديد</Link></li>
              <li><Link to="/history" className="text-white/60 hover:text-white transition">السجل</Link></li>
              <li><Link to="/emergency" className="text-white/60 hover:text-white transition">دليل الطوارئ</Link></li>
              <li><Link to="/profile" className="text-white/60 hover:text-white transition">الملف الصحي</Link></li>
            </ul>
          </div>

          <div>
            <h4 className="text-white font-semibold text-sm mb-3">في حالة الطوارئ</h4>
            <a
              href="tel:911"
              className="inline-flex items-center gap-2 bg-danger text-white px-4 py-2.5 rounded-xl font-semibold shadow-soft hover:brightness-110 transition"
            >
              <Phone size={15} />
              اتصل بالإسعاف 911
            </a>
            <p className="flex items-start gap-1.5 text-xs text-white/50 mt-3 leading-relaxed">
              <ShieldAlert size={14} className="shrink-0 mt-0.5" />
              هذا التطبيق ليس بديلاً عن الاستشارة الطبية المتخصصة.
            </p>
          </div>
        </div>

        <div className="border-t border-white/10 mt-8 pt-5 text-center sm:text-start text-xs text-white/40">
          © {year} ميديك زيرو — جميع الحقوق محفوظة.
        </div>
      </div>
    </footer>
  );
}
