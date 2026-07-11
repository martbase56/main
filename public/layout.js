// public/layout.js
// MerketBaseBD - Optimized Global Layout Engine with Hybrid Caching (Zero Latency)

document.addEventListener('DOMContentLoaded', async () => {
    // ১. পেজে হেডার এবং ফুটার প্লেসহোল্ডার থাকলে স্বয়ংক্রিয়ভাবে ইনজেক্ট করা
    injectHeaderAndFooter();
    
    // ২. হাইব্রিড ক্যাশিং ইঞ্জিনের মাধ্যমে জিরো-ল্যাটেন্সি সুপাবেস ইনিশিয়ালাইজেশন
    await initLayoutSupabase();
});

let supabaseClient = null;

async function initLayoutSupabase() {
    // ক. প্রথমে ব্রাউজারের লোকাল মেমোরি (Cache) থেকে কনফিগ চেক করা
    const cachedConfig = localStorage.getItem('supabase_config');
    if (cachedConfig) {
        try {
            const config = JSON.parse(cachedConfig);
            if (config.supabase_url && config.supabase_anon_key) {
                // ক্যাশ ডাটা থাকলে সরাসরি ইনস্ট্যান্ট সুপাবেস ক্লায়েন্ট সচল করা (০ মিলি-সেকেন্ড বিলম্ব!)
                supabaseClient = window.supabase.createClient(config.supabase_url, config.supabase_anon_key);
                window.supabaseClient = supabaseClient;
                
                // ব্যাকগ্রাউন্ডে সাইডবার ও ব্যাজ আপডেট শুরু করা
                updateLayoutNavigation();
                updateLayoutBadges();
                console.log("⚡ Supabase Client initialized instantly from local browser cache.");
            }
        } catch (e) {
            localStorage.removeItem('supabase_config');
        }
    }

    // খ. ব্যাকগ্রাউন্ডে (ইউজারের লোডিং স্ক্রিন ব্লক না করে) লেটেস্ট ভেরিয়েবল রিড করা
    try {
        const response = await fetch('/api/auth/config');
        if (response.ok) {
            const config = await response.json();
            if (config.supabase_url && config.supabase_anon_key) {
                // পরবর্তী ভিজিটের জন্য ক্যাশ মেমোরি আপডেট করে রাখা
                localStorage.setItem('supabase_config', JSON.stringify(config));
                
                // যদি পূর্বে ক্যাশ না থাকার কারণে ক্লায়েন্ট তৈরি না হয়ে থাকে, তবে এখন ইনিশিয়েট হবে
                if (!supabaseClient) {
                    supabaseClient = window.supabase.createClient(config.supabase_url, config.supabase_anon_key);
                    window.supabaseClient = supabaseClient;
                    await updateLayoutNavigation();
                    updateLayoutBadges();
                    console.log("🔄 Supabase Client initialized from fresh background fetch.");
                }
            }
        }
    } catch (err) {
        console.error("Background config fetch failed:", err);
    }
}

// হেডার-ফুটার ইনজেকশন ফাংশন
function injectHeaderAndFooter() {
    const headerPlaceholder = document.getElementById('header-placeholder');
    const footerPlaceholder = document.getElementById('footer-placeholder');

    if (headerPlaceholder) {
        headerPlaceholder.innerHTML = `
            <header class="bg-gradient-to-r from-[#FF6B00] to-[#FF8C33] sticky top-0 z-50 shadow-md shadow-primary/10 border-b border-white/10">
                <div class="max-w-[1200px] mx-auto px-5 py-4 flex justify-between items-center w-full">
                    <a href="/" class="font-headings font-extrabold text-3xl text-white tracking-tight hover:scale-[1.02] transition-transform">MerketBaseBD</a>
                    
                    <button class="menu-toggle lg:hidden text-2xl text-white focus:outline-none" id="menu-toggle">
                        <i class="fa-solid fa-bars" id="menu-icon"></i>
                    </button>

                    <ul class="hidden lg:flex lg:flex-row lg:items-center lg:gap-6 lg:static absolute top-[70px] left-0 w-full bg-gradient-to-b from-[#FF6B00] to-[#FF8C33] lg:bg-transparent px-6 py-6 lg:p-0 flex-col items-start lg:items-center gap-5 shadow-lg lg:shadow-none z-50 border-t border-white/10 lg:border-none list-none ml-auto text-left" id="nav-menu">
                        <li class="w-full"><a href="/" class="nav-link w-full text-left font-bold text-[0.95rem] text-white hover:text-white/80 flex items-center gap-1.5 transition-colors py-1"><i class="fa-solid fa-house"></i> হোম</a></li>
                        <li class="w-full"><a href="/#products-section" class="nav-link w-full text-left font-bold text-[0.95rem] text-white hover:text-white/80 flex items-center gap-1.5 transition-colors py-1"><i class="fa-solid fa-basket-shopping"></i> প্রোডাক্টস</a></li>
                        <li class="w-full"><a href="/#offers-section" class="nav-link w-full text-left font-bold text-[0.95rem] text-white hover:text-white/80 flex items-center gap-1.5 transition-colors py-1"><i class="fa-solid fa-tag"></i> অফারসমূহ</a></li>
                        <li class="w-full"><a href="/earning" class="nav-link w-full text-left font-bold text-[0.95rem] text-white hover:text-white/80 flex items-center gap-1.5 transition-colors py-1"><i class="fa-solid fa-coins"></i> আর্ন জোন</a></li>
                        <li class="w-full"><a href="/digital-services" class="nav-link w-full text-left font-bold text-[0.95rem] text-white hover:text-white/80 flex items-center gap-1.5 transition-colors py-1"><i class="fa-solid fa-laptop-code"></i> ডিজিটাল সার্ভিস</a></li>
                        <li class="w-full"><a href="/checkout" class="nav-link w-full text-left font-bold text-[0.95rem] text-white hover:text-white/80 flex items-center gap-1.5 transition-colors py-1"><i class="fa-solid fa-cart-shopping"></i> কার্ট (<span id="cart-count">0</span>)</a></li>
                        <li class="w-full"><a href="/profile?tab=wishlist" class="nav-link w-full text-left font-bold text-[0.95rem] text-white hover:text-white/80 flex items-center gap-1.5 transition-colors py-1"><i class="fa-solid fa-heart text-red-500"></i> পছন্দের তালিকা (<span id="fav-count">0</span>)</a></li>
                        
                        <li id="dynamic-nav" class="w-full lg:w-auto">
                            <a href="/login" class="block text-center font-bold text-[0.95rem] bg-primary text-white py-2.5 px-6 rounded-full hover:bg-white/90 transition-all shadow-md">লগইন</a>
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
                
                if (navMenu.classList.contains('hidden')) {
                    menuIcon.className = "fa-solid fa-bars text-white";
                } else {
                    menuIcon.className = "fa-solid fa-xmark text-white";
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
                            বাংলাদেশের সেরা প্রিমিয়াম রিসেলিং ও ওয়ার্ক প্ল্যাটফর্ম। আধুনিক উপায়ে কেনাকাটা এবং স্বনির্ভরতা অর্জনে আমরা সর্বদা আপনার পাশে আছি।
                        </p>
                        <div class="footer-socials flex gap-3 pt-2">
                            <a href="https://facebook.com" class="w-10 h-10 bg-white/10 border border-white/10 rounded-full flex items-center justify-center text-white hover:bg-white hover:text-[#FF6B00] hover:scale-110 transition-all" target="_blank"><i class="fa-brands fa-facebook-f text-sm"></i></a>
                            <a href="https://youtube.com" class="w-10 h-10 bg-white/10 border border-white/10 rounded-full flex items-center justify-center text-white hover:bg-white hover:text-[#FF6B00] hover:scale-110 transition-all" target="_blank"><i class="fa-brands fa-youtube text-sm"></i></a>
                            <a href="https://telegram.org" class="w-10 h-10 bg-white/10 border border-white/10 rounded-full flex items-center justify-center text-white hover:bg-white hover:text-[#FF6B00] hover:scale-110 transition-all" target="_blank"><i class="fa-brands fa-telegram text-sm"></i></a>
                            <a href="https://whatsapp.com" class="w-10 h-10 bg-white/10 border border-white/10 rounded-full flex items-center justify-center text-white hover:bg-white hover:text-[#FF6B00] hover:scale-110 transition-all" target="_blank"><i class="fa-brands fa-whatsapp text-sm"></i></a>
                        </div>
                    </div>
                    <div class="footer-col">
                        <h4 class="text-white text-[1.15rem] font-bold mb-6 relative pb-2 after:content-[''] after:absolute after:bottom-0 after:left-0 after:w-6 after:h-[3px] after:bg-white after:rounded-full">মেনু লিঙ্কসমূহ</h4>
                        <ul class="footer-links list-none text-sm space-y-3">
                            <li><a href="/" class="hover:translate-x-1.5 text-white/80 hover:text-white transition-all inline-block"><i class="fa-solid fa-chevron-right text-[0.7rem] text-white mr-1"></i> হোম</a></li>
                            <li><a href="/#products-section" class="hover:translate-x-1.5 text-white/80 hover:text-white transition-all inline-block"><i class="fa-solid fa-chevron-right text-[0.7rem] text-white mr-1"></i> প্রোডাক্টস</a></li>
                            <li><a href="/#offers-section" class="hover:translate-x-1.5 text-white/80 hover:text-white transition-all inline-block"><i class="fa-solid fa-chevron-right text-[0.7rem] text-white mr-1"></i> অফারসমূহ</a></li>
                            <li><a href="/earning" class="hover:translate-x-1.5 text-white/80 hover:text-white transition-all inline-block"><i class="fa-solid fa-chevron-right text-[0.7rem] text-white mr-1"></i> আর্ন জোন</a></li>
                            <li><a href="/digital-services" class="hover:translate-x-1.5 text-white/80 hover:text-white transition-all inline-block"><i class="fa-solid fa-chevron-right text-[0.7rem] text-white mr-1"></i> ডিজিটাল সার্ভিস</a></li>
                        </ul>
                    </div>
                    <div class="footer-col">
                        <h4 class="text-white text-[1.15rem] font-bold mb-6 relative pb-2 after:content-[''] after:absolute after:bottom-0 after:left-0 after:w-6 after:h-[3px] after:bg-white after:rounded-full">পলিসি ও গাইডলাইন</h4>
                        <ul class="footer-links list-none text-sm space-y-3">
                            <li><a href="/about" class="hover:translate-x-1.5 text-white/80 hover:text-white transition-all inline-block"><i class="fa-solid fa-chevron-right text-[0.7rem] text-white mr-1"></i> আমাদের সম্পর্কে</a></li>
                            <li><a href="/contact" class="hover:translate-x-1.5 text-white/80 hover:text-white transition-all inline-block"><i class="fa-solid fa-chevron-right text-[0.7rem] text-white mr-1"></i> যোগাযোগ করুন</a></li>
                            <li><a href="/privacy" class="hover:translate-x-1.5 text-white/80 hover:text-white transition-all inline-block"><i class="fa-solid fa-chevron-right text-[0.7rem] text-white mr-1"></i> গোপনীয়তা নীতি</a></li>
                            <li><a href="/refund-policy" class="hover:translate-x-1.5 text-white/80 hover:text-white transition-all inline-block"><i class="fa-solid fa-chevron-right text-[0.7rem] text-white mr-1"></i> রিফান্ড পলিসি</a></li>
                            <li><a href="/reseller-policy" class="hover:translate-x-1.5 text-white/80 hover:text-white transition-all inline-block"><i class="fa-solid fa-chevron-right text-[0.7rem] text-white mr-1"></i> রিসেলার পলিসি</a></li>
                            <li><a href="/report" class="hover:translate-x-1.5 text-white/80 hover:text-white transition-all inline-block"><i class="fa-solid fa-chevron-right text-[0.7rem] text-white mr-1"></i> অভিযোগ ও রিপোর্ট</a></li>
                        </ul>
                    </div>
                    <div class="footer-col space-y-4">
                        <h4 class="text-white text-[1.15rem] font-bold mb-6 relative pb-2 after:content-[''] after:absolute after:bottom-0 after:left-0 after:w-6 after:h-[3px] after:bg-white after:rounded-full">পেমেন্ট মেথডস</h4>
                        <p class="text-sm leading-relaxed mb-4 text-white/90">নিরাপদ ও নির্ভরযোগ্য মোবাইল ব্যাংকিং গেটওয়ের মাধ্যমে আপনার পেমেন্ট সম্পন্ন করুন নিশ্চিন্তে।</p>
                        <div class="payment-gateways flex flex-wrap gap-2.5 pt-1">
                            <span class="gateway-badge bg-white text-[#FF6B00] px-4 py-1.5 rounded-lg text-xs font-extrabold tracking-wide transition-all cursor-default">bKash</span>
                            <span class="gateway-badge bg-white text-[#FF6B00] px-4 py-1.5 rounded-lg text-xs font-extrabold tracking-wide transition-all cursor-default">Nagad</span>
                            <span class="gateway-badge bg-white text-[#FF6B00] px-4 py-1.5 rounded-lg text-xs font-extrabold tracking-wide transition-all cursor-default">Rocket</span>
                        </div>
                    </div>
                </div>
                <div class="copyright-bar border-t border-white/10 pt-6 text-center text-sm text-white/70 max-w-[1200px] mx-auto">
                    <p>&copy; 2026 MerketBaseBD Premium Work & Earn Platform. All rights reserved. | Developed by <a href="https://github.com/alihosen" class="text-white hover:underline font-semibold" target="_blank">Ali Hosen</a></p>
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
                        <li class="w-full"><a href="/dashboard/reseller" class="nav-link w-full text-left font-bold text-[0.95rem] text-white hover:text-white/80 flex items-center gap-1.5 transition-colors py-1"><i class="fa-solid fa-chart-line"></i> ওয়ার্কার প্যানেল</a></li>
                        <li class="w-full mt-2 lg:mt-0 lg:w-auto"><a href="#" onclick="handleLayoutLogout()" class="nav-link block text-center font-bold text-[0.95rem] bg-white/10 border border-white/20 text-white py-2.5 px-6 rounded-full hover:bg-white/20 transition-all shadow-md"><i class="fa-solid fa-arrow-right-from-bracket"></i> লগআউট</a></li>
                    `;
                } else if (profile.role === 'admin') {
                    dynamicNav.outerHTML = `
                        <li class="w-full"><a href="/dashboard/admin" class="nav-link w-full text-left font-bold text-[0.95rem] text-white hover:text-white/80 flex items-center gap-1.5 transition-colors py-1"><i class="fa-solid fa-chart-line"></i> এডমিন প্যানেল</a></li>
                        <li class="w-full mt-2 lg:mt-0 lg:w-auto"><a href="#" onclick="handleLayoutLogout()" class="nav-link block text-center font-bold text-[0.95rem] bg-white/10 border border-white/20 text-white py-2.5 px-6 rounded-full hover:bg-white/20 transition-all shadow-md"><i class="fa-solid fa-arrow-right-from-bracket"></i> লগআউট</a></li>
                    `;
                } else {
                    dynamicNav.outerHTML = `
                        <li class="w-full"><a href="/profile" class="nav-link w-full text-left font-bold text-[0.95rem] text-white hover:text-white/80 flex items-center gap-1.5 transition-colors py-1"><i class="fa-solid fa-user-gear"></i> প্রোফাইল</a></li>
                        <li class="w-full"><a href="/checkout" class="nav-link w-full text-left font-bold text-[0.95rem] text-white hover:text-white/80 flex items-center gap-1.5 transition-colors py-1"><i class="fa-solid fa-credit-card"></i> চেকআউট</a></li>
                        <li class="w-full mt-2 lg:mt-0 lg:w-auto"><a href="#" onclick="handleLayoutLogout()" class="nav-link block text-center font-bold text-[0.95rem] bg-white/10 border border-white/20 text-white py-2.5 px-6 rounded-full hover:bg-white/20 transition-all shadow-md"><i class="fa-solid fa-arrow-right-from-bracket"></i> লগআউট</a></li>
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
