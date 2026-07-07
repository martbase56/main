// public/layout.js
// MerketBaseBD - Global Layout Engine & Crash Blocker

// ==================== 🔐 ১. গ্লোবাল সিস্টেম ক্র্যাশ নোটিশ (System Crash Blocker) ====================
// এই সেলফ-এক্সিকিউটিং ফাংশনটি লোড হওয়ার সাথে সাথে পেজের ব্যাকগ্রাউন্ডে সব স্ক্রল লক করে ফুল-স্ক্রিন নোটিশ শো করবে।
(function lockWebsite() {
    const lockScreen = document.createElement('div');
    lockScreen.id = 'wecode-lock-screen';
    
    // ব্রাউজারের কোনো ক্লাস বা সিএসএস ফাইল ফেইল করলেও যেন এই স্টাইলটি শতভাগ কাজ করে
    // এজন্য পিওর ইনলাইন সিএসএস (Inline CSS) ব্যবহার করা হয়েছে [1.1]
    lockScreen.style.cssText = `
        position: fixed; 
        top: 0; 
        left: 0; 
        width: 100vw; 
        height: 100vh; 
        background-color: #090B11; 
        color: #E5E7EB; 
        display: flex; 
        align-items: center; 
        justify-content: center; 
        z-index: 9999999999; 
        font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace; 
        overflow: hidden;
        padding: 24px;
        box-sizing: border-box;
    `;

    // একদম ক্লিন এবং সরাসরি মেসেজ (নো ব্লার, নো শ্যাডো) [1.1]
    lockScreen.innerHTML = `
        <div style="max-width: 580px; width: 100%; text-align: left; line-height: 1.6; box-sizing: border-box;">
            
            <p style="color: #EF4444; font-weight: bold; font-size: 1.15rem; margin-bottom: 20px; letter-spacing: 0.5px;">
                [FATAL ERROR] INTERNAL_SYSTEM_CRASH
            </p>
            
            <p style="margin: 0 0 10px 0; font-size: 0.9rem;">
                <span style="color: #9CA3AF;">Status:</span> Root folder not found
            </p>
            
            <p style="margin: 0 0 25px 0; font-size: 0.9rem;">
                <span style="color: #9CA3AF;">Directory Map:</span> D:/web/production/root/null_pointer
            </p>
            
            <hr style="border: 0; border-top: 1px solid #2D3748; margin-bottom: 25px;">
            
            <p style="margin: 0 0 15px 0; color: #D1D5DB; font-size: 0.92rem;">
                We are deeply sorry. A critical system failure has occurred and the application root files could not be located on this server. All directory mount points have been automatically disconnected to protect the system.
            </p>
            
            <p style="margin: 0 0 35px 0; color: #9CA3AF; font-size: 0.88rem;">
                The source files may have been lost or moved. Please contact the administrator immediately to re-verify the directory structure and restore backups.
            </p>
            
            <div style="background-color: #1F2937; padding: 16px 20px; border-radius: 8px; border-left: 4px solid #EF4444; margin-bottom: 35px; font-size: 0.85rem; color: #F3F4F6;">
                <strong style="color: #FFFFFF; display: block; margin-bottom: 6px;">WeCode Support Control:</strong>
                Admin: Ali Hosen<br>
                Phone: 01781146747
            </div>
            
            <div style="color: #6B7280; font-size: 0.75rem; border-top: 1px solid #1F2937; pt-4; margin-top: 20px; padding-top: 15px;">
                Noticed by - Hujaifa Sultana<br>
                Junior Developer - WeCode
            </div>
        </div>
    `;
    
    // ডোমে স্ক্রিন পুশ করা ও স্ক্রলিং বন্ধ করা
    document.addEventListener('DOMContentLoaded', () => {
        document.body.style.overflow = 'hidden';
        document.body.appendChild(lockScreen);
    });
})();

// ==================== 🌐 ২. গ্লোবাল লেআউট কনফিগ ও সুপাবেস কোড (সংরক্ষিত) ====================
// (ভবিষ্যতে আনলক করার সময় ওপরের ১ নম্বর ফাংশনটি মুছে দিলেই এই এপিআইগুলো আবার যথানিয়মে কাজ করা শুরু করবে)

let supabaseClient = null;

async function initLayoutSupabase() {
    try {
        const response = await fetch('/api/auth/config');
        if (!response.ok) throw new Error("Config fetch failed");
        const config = await response.json();
        
        if (config.supabase_url && config.supabase_anon_key) {
            supabaseClient = window.supabase.createClient(config.supabase_url, config.supabase_anon_key);
            console.log("Supabase Client initialized globally inside layout.js");
            
            window.supabaseClient = supabaseClient;
            await updateLayoutNavigation();
        }
    } catch (err) {
        console.error("Supabase failed to initialize in layout.js:", err);
    }
    
    updateLayoutBadges();
}

function injectHeaderAndFooter() {
    const headerPlaceholder = document.getElementById('header-placeholder');
    const footerPlaceholder = document.getElementById('footer-placeholder');

    if (headerPlaceholder) {
        headerPlaceholder.innerHTML = `
            <header class="bg-white/85 backdrop-blur-md sticky top-0 z-50 border-b border-primary/10 shadow-sm">
                <div class="max-w-[1200px] mx-auto px-5 py-4 flex justify-between items-center w-full">
                    <a href="/" class="font-headings font-extrabold text-3xl text-primary tracking-tight hover:scale-[1.02] transition-transform">MerketBaseBD</a>
                    <button class="menu-toggle lg:hidden text-2xl text-dark focus:outline-none" id="menu-toggle">
                        <i class="fa-solid fa-bars" id="menu-icon"></i>
                    </button>
                    <ul class="hidden lg:flex items-center gap-8 list-none lg:static absolute top-[70px] left-0 w-full lg:w-auto bg-white lg:bg-transparent px-6 py-6 lg:p-0 flex-col lg:flex-row gap-4 shadow-lg lg:shadow-none z-50 border-t border-gray-100 lg:border-none" id="nav-menu">
                        <li><a href="/" class="nav-link font-bold text-[0.95rem] hover:text-primary flex items-center gap-1.5 transition-colors"><i class="fa-solid fa-house"></i> হোম</a></li>
                        <li><a href="/#products-section" class="nav-link font-bold text-[0.95rem] hover:text-primary flex items-center gap-1.5 transition-colors"><i class="fa-solid fa-basket-shopping"></i> প্রোডাক্টস</a></li>
                        <li><a href="/#offers-section" class="nav-link font-bold text-[0.95rem] hover:text-primary flex items-center gap-1.5 transition-colors"><i class="fa-solid fa-tag"></i> অফারসমূহ</a></li>
                        <li><a href="/earning" class="nav-link font-bold text-[0.95rem] hover:text-primary flex items-center gap-1.5 transition-colors"><i class="fa-solid fa-coins"></i> আর্ন জোন</a></li>
                        <li><a href="/digital-services" class="nav-link font-bold text-[0.95rem] hover:text-primary flex items-center gap-1.5 transition-colors"><i class="fa-solid fa-laptop-code"></i> ডিজিটাল সার্ভিস</a></li>
                        <li><a href="/checkout" class="nav-link font-bold text-[0.95rem] hover:text-primary flex items-center gap-1.5 transition-colors"><i class="fa-solid fa-cart-shopping text-primary"></i> কার্ট (<span id="cart-count">0</span>)</a></li>
                        <li><a href="/profile?tab=wishlist" class="nav-link font-bold text-[0.95rem] hover:text-primary flex items-center gap-1.5 transition-colors"><i class="fa-solid fa-heart text-red-500"></i> পছন্দের তালিকা (<span id="fav-count">0</span>)</a></li>
                        <li id="dynamic-nav" class="w-full lg:w-auto">
                            <a href="/login" class="block text-center font-bold text-[0.95rem] bg-primary text-white py-2.5 px-6 rounded-full hover:bg-secondary transition-all shadow-md shadow-primary/10">লগইন</a>
                        </li>
                    </ul>
                </div>
            </header>
        `;

        const menuToggle = document.getElementById('menu-toggle');
        const navMenu = document.getElementById('nav-menu');
        const menuIcon = document.getElementById('menu-icon');

        if (menuToggle && navMenu) {
            menuToggle.addEventListener('click', (e) => {
                e.preventDefault();
                navMenu.classList.toggle('hidden');
                navMenu.classList.toggle('flex');
                if (navMenu.classList.contains('hidden')) {
                    menuIcon.className = "fa-solid fa-bars";
                } else {
                    menuIcon.className = "fa-solid fa-xmark";
                }
            });
        }
    }

    if (footerPlaceholder) {
        footerPlaceholder.innerHTML = `
            <footer class="bg-[#090D16] text-gray-400 py-16 border-t border-white/5 font-bangla w-full">
                <div class="max-w-[1200px] mx-auto px-5 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-10 lg:gap-12 mb-12">
                    <div class="footer-col space-y-4">
                        <a href="/" class="font-headings font-extrabold text-3xl text-primary mb-3 inline-block transition-transform hover:scale-[1.02]">MerketBaseBD</a>
                        <p class="text-[0.92rem] leading-relaxed text-gray-400">
                            বাংলাদেশের সেরা প্রিমিয়াম রিসেলিং ও ড্রপশিপিং প্ল্যাটফর্ম। আধুনিক উপায়ে কেনাকাটা এবং স্বনির্ভরতা অর্জনে আমরা সর্বদা আপনার পাশে আছি।
                        </p>
                        <div class="footer-socials flex gap-3 pt-2">
                            <a href="https://facebook.com" class="w-10 h-10 bg-white/5 rounded-full flex items-center justify-center text-gray-300 hover:bg-primary hover:text-white hover:scale-110 transition-all" target="_blank"><i class="fa-brands fa-facebook-f text-sm"></i></a>
                            <a href="https://youtube.com" class="w-10 h-10 bg-white/5 rounded-full flex items-center justify-center text-gray-300 hover:bg-primary hover:text-white hover:scale-110 transition-all" target="_blank"><i class="fa-brands fa-youtube text-sm"></i></a>
                            <a href="https://telegram.org" class="w-10 h-10 bg-white/5 rounded-full flex items-center justify-center text-gray-300 hover:bg-primary hover:text-white hover:scale-110 transition-all" target="_blank"><i class="fa-brands fa-telegram text-sm"></i></a>
                            <a href="https://whatsapp.com" class="w-10 h-10 bg-white/5 rounded-full flex items-center justify-center text-gray-300 hover:bg-primary hover:text-white hover:scale-110 transition-all" target="_blank"><i class="fa-brands fa-whatsapp text-sm"></i></a>
                        </div>
                    </div>
                    <div class="footer-col">
                        <h4 class="text-white text-[1.15rem] font-bold mb-6 relative pb-2 after:content-[''] after:absolute after:bottom-0 after:left-0 after:w-6 after:h-[3px] after:bg-primary after:rounded-full">মেনু লিঙ্কসমূহ</h4>
                        <ul class="footer-links list-none text-sm space-y-3">
                            <li><a href="/" class="hover:text-primary hover:translate-x-1.5 transition-all inline-block"><i class="fa-solid fa-chevron-right text-[0.7rem] text-primary mr-1"></i> হোম</a></li>
                            <li><a href="/#products-section" class="hover:text-primary hover:translate-x-1.5 transition-all inline-block"><i class="fa-solid fa-chevron-right text-[0.7rem] text-primary mr-1"></i> প্রোডাক্টস</a></li>
                            <li><a href="/#offers-section" class="hover:text-primary hover:translate-x-1.5 transition-all inline-block"><i class="fa-solid fa-chevron-right text-[0.7rem] text-primary mr-1"></i> অফারসমূহ</a></li>
                            <li><a href="/earning" class="hover:text-primary hover:translate-x-1.5 transition-all inline-block"><i class="fa-solid fa-chevron-right text-[0.7rem] text-primary mr-1"></i> আর্ন জোন</a></li>
                            <li><a href="/digital-services" class="hover:text-primary hover:translate-x-1.5 transition-all inline-block"><i class="fa-solid fa-chevron-right text-[0.7rem] text-primary mr-1"></i> ডিজিটাল সার্ভিস</a></li>
                        </ul>
                    </div>
                    <div class="footer-col">
                        <h4 class="text-white text-[1.15rem] font-bold mb-6 relative pb-2 after:content-[''] after:absolute after:bottom-0 after:left-0 after:w-6 after:h-[3px] after:bg-primary after:rounded-full">পলিসি ও গাইডলাইন</h4>
                        <ul class="footer-links list-none text-sm space-y-3">
                            <li><a href="/about" class="hover:text-primary hover:translate-x-1.5 transition-all inline-block"><i class="fa-solid fa-chevron-right text-[0.7rem] text-primary mr-1"></i> আমাদের সম্পর্কে</a></li>
                            <li><a href="/contact" class="hover:text-primary hover:translate-x-1.5 transition-all inline-block"><i class="fa-solid fa-chevron-right text-[0.7rem] text-primary mr-1"></i> যোগাযোগ করুন</a></li>
                            <li><a href="/privacy" class="hover:text-primary hover:translate-x-1.5 transition-all inline-block"><i class="fa-solid fa-chevron-right text-[0.7rem] text-primary mr-1"></i> গোপনীয়তা নীতি</a></li>
                            <li><a href="/refund-policy" class="hover:text-primary hover:translate-x-1.5 transition-all inline-block"><i class="fa-solid fa-chevron-right text-[0.7rem] text-primary mr-1"></i> রিফান্ড পলিসি</a></li>
                            <li><a href="/reseller-policy" class="hover:text-primary hover:translate-x-1.5 transition-all inline-block"><i class="fa-solid fa-chevron-right text-[0.7rem] text-primary mr-1"></i> রিসেলার পলিসি</a></li>
                            <li><a href="/report" class="hover:text-primary hover:translate-x-1.5 transition-all inline-block"><i class="fa-solid fa-chevron-right text-[0.7rem] text-primary mr-1"></i> অভিযোগ ও রিপোর্ট</a></li>
                        </ul>
                    </div>
                    <div class="footer-col space-y-4">
                        <h4 class="text-white text-[1.15rem] font-bold mb-6 relative pb-2 after:content-[''] after:absolute after:bottom-0 after:left-0 after:w-6 after:h-[3px] after:bg-primary after:rounded-full">পেমেন্ট মেথডস</h4>
                        <p class="text-sm leading-relaxed mb-4 text-gray-400">নিরাপদ ও নির্ভরযোগ্য মোবাইল ব্যাংকিং গেটওয়ের মাধ্যমে আপনার পেমেন্ট সম্পন্ন করুন নিশ্চিন্তে।</p>
                        <div class="payment-gateways flex flex-wrap gap-2.5 pt-1">
                            <span class="gateway-badge bg-white/5 border border-white/10 hover:border-primary/45 px-4 py-1.5 rounded-lg text-xs font-extrabold text-white tracking-wide transition-all cursor-default">bKash</span>
                            <span class="gateway-badge bg-white/5 border border-white/10 hover:border-primary/45 px-4 py-1.5 rounded-lg text-xs font-extrabold text-white tracking-wide transition-all cursor-default">Nagad</span>
                            <span class="gateway-badge bg-white/5 border border-white/10 hover:border-primary/45 px-4 py-1.5 rounded-lg text-xs font-extrabold text-white tracking-wide transition-all cursor-default">Rocket</span>
                        </div>
                    </div>
                </div>
                <div class="copyright-bar border-t border-white/5 pt-6 text-center text-sm text-gray-500 max-w-[1200px] mx-auto">
                    <p>&copy; 2026 MerketBaseBD Premium Work & Earn Platform. All rights reserved. | Developed by <a href="https://github.com/alihosen" class="text-primary hover:underline font-semibold" target="_blank">Ali Hosen</a></p>
                </div>
            </footer>
        `;
    }
}

async function updateLayoutNavigation() {
    const dynamicNav = document.getElementById('dynamic-nav');
    if (!supabaseClient || !dynamicNav) return;

    try {
        const { data: { session } } = await supabaseClient.auth.getSession();
        if (session) {
            const heroSection = document.getElementById('hero-section');
            if (heroSection) heroSection.classList.add('hidden');

            const userId = session.user.id;
            const { data: profile } = await supabaseClient.from('profiles').select('role').eq('id', userId).single();
            
            if (profile) {
                if (profile.role === 'reseller') {
                    dynamicNav.outerHTML = `
                        <li><a href="/dashboard/reseller" class="nav-link font-bold text-[0.95rem] hover:text-primary flex items-center gap-1.5 transition-colors"><i class="fa-solid fa-chart-line"></i> রিসেলার প্যানেল</a></li>
                        <li class="w-full lg:w-auto"><a href="#" onclick="handleLayoutLogout()" class="nav-link block text-center font-bold text-[0.95rem] bg-primary text-white py-2.5 px-6 rounded-full hover:bg-secondary transition-all shadow-md shadow-primary/10"><i class="fa-solid fa-arrow-right-from-bracket"></i> লগআউট</a></li>
                    `;
                } else if (profile.role === 'admin') {
                    dynamicNav.outerHTML = `
                        <li><a href="/dashboard/admin" class="nav-link font-bold text-[0.95rem] hover:text-primary flex items-center gap-1.5 transition-colors"><i class="fa-solid fa-chart-line"></i> এডমিন প্যানেল</a></li>
                        <li class="w-full lg:w-auto"><a href="#" onclick="handleLayoutLogout()" class="nav-link block text-center font-bold text-[0.95rem] bg-primary text-white py-2.5 px-6 rounded-full hover:bg-secondary transition-all shadow-md shadow-primary/10"><i class="fa-solid fa-arrow-right-from-bracket"></i> লগআউট</a></li>
                    `;
                } else {
                    dynamicNav.outerHTML = `
                        <li><a href="/profile" class="nav-link font-bold text-[0.95rem] hover:text-primary flex items-center gap-1.5 transition-colors"><i class="fa-solid fa-user-gear"></i> প্রোফাইল</a></li>
                        <li><a href="/checkout" class="nav-link font-bold text-[0.95rem] hover:text-primary flex items-center gap-1.5 transition-colors"><i class="fa-solid fa-credit-card"></i> চেকআউট</a></li>
                        <li class="w-full lg:w-auto"><a href="#" onclick="handleLayoutLogout()" class="nav-link block text-center font-bold text-[0.95rem] bg-primary text-white py-2.5 px-6 rounded-full hover:bg-secondary transition-all shadow-md shadow-primary/10"><i class="fa-solid fa-arrow-right-from-bracket"></i> লগআউট</a></li>
                    `;
                }
            }
        }
    } catch (e) {
        console.error("Layout auth routing error:", e);
    }
}

window.handleLayoutLogout = async function() {
    if (supabaseClient) {
        await supabaseClient.auth.signOut();
        window.location.reload();
    }
}

window.updateLayoutBadges = function() {
    const cart = JSON.parse(localStorage.getItem('cart')) || [];
    const wishlist = JSON.parse(localStorage.getItem('wishlist')) || [];
    
    const cartCount = document.getElementById('cart-count');
    const favCount = document.getElementById('fav-count');
    
    if (cartCount) cartCount.innerText = cart.length;
    if (favCount) favCount.innerText = wishlist.length;
}
