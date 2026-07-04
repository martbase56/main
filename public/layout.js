// public/layout.js
// এই ফাইলটি আপনার ওয়েবসাইটের সমস্ত পেজের হেডার, ফুটার, কার্ট ও সুপাবেস কানেকশন কন্ট্রোল করবে।

document.addEventListener('DOMContentLoaded', async () => {
    // ১. পেজে হেডার এবং ফুটার প্লেসহোল্ডার থাকলে স্বয়ংক্রিয়ভাবে ইনজেক্ট করা
    injectHeaderAndFooter();
    
    // ২. ডাইনামিক সুপাবেস কানেকশন ও মেম্বার সেশন চেক
    await initLayoutSupabase();
});

let supabaseClient = null;

async function initLayoutSupabase() {
    try {
        const response = await fetch('/api/auth/config');
        if (!response.ok) throw new Error("Config fetch failed");
        const config = await response.json();
        
        if (config.supabase_url && config.supabase_anon_key) {
            // সুপাবেস ক্লায়েন্ট ইনিশিয়ালাইজেশন
            supabaseClient = window.supabase.createClient(config.supabase_url, config.supabase_anon_key);
            console.log("Supabase Client initialized globally inside layout.js");
            
            // অন্যান্য পেজে ব্যবহারের সুবিধার জন্য এটিকে গ্লোবালি এক্সপোজ করা হলো
            window.supabaseClient = supabaseClient;
            
            // লগইন স্ট্যাটাস অনুযায়ী নেভিগেশন বার ও হিরো সেকশন কন্ট্রোল
            await updateLayoutNavigation();
        }
    } catch (err) {
        console.error("Supabase failed to initialize in layout.js:", err);
    }
    
    // কার্ট এবং উইশলিস্ট কাউন্টার আপডেট করা
    updateLayoutBadges();
}

// ৩. ডাইনামিক হেডার ও ফুটার HTML ইনজেকশন ফাংশন
function injectHeaderAndFooter() {
    const headerPlaceholder = document.getElementById('header-placeholder');
    const footerPlaceholder = document.getElementById('footer-placeholder');

    // ক. ইউনিফাইড হেডার রেন্ডারিং
    if (headerPlaceholder) {
        headerPlaceholder.innerHTML = `
            <header class="bg-white/85 backdrop-blur-md sticky top-0 z-50 border-b border-primary/10 shadow-sm">
                <div class="max-w-[1200px] mx-auto px-5 py-4 flex justify-between items-center">
                    <a href="/" class="font-headings font-extrabold text-3xl text-primary tracking-tight hover:scale-[1.02] transition-transform">MartBaseBD</a>
                    
                    <button class="lg:hidden text-2xl text-dark focus:outline-none" id="menu-toggle">
                        <i class="fa-solid fa-bars" id="menu-icon"></i>
                    </button>

                    <ul class="hidden lg:flex items-center gap-6 list-none lg:static absolute top-[70px] left-0 w-full lg:w-auto bg-white lg:bg-transparent px-6 py-6 lg:p-0 flex-col lg:flex-row gap-4 shadow-lg lg:shadow-none z-50 border-t border-gray-100 lg:border-none" id="nav-menu">
                        <li><a href="/" class="nav-link font-semibold text-[0.95rem] hover:text-primary flex items-center gap-1.5 transition-colors"><i class="fa-solid fa-house"></i> হোম</a></li>
                        <li><a href="/#products-section" class="nav-link font-semibold text-[0.95rem] hover:text-primary flex items-center gap-1.5 transition-colors"><i class="fa-solid fa-basket-shopping"></i> প্রোডাক্টস</a></li>
                        <li><a href="/#offers-section" class="nav-link font-semibold text-[0.95rem] hover:text-primary flex items-center gap-1.5 transition-colors"><i class="fa-solid fa-tag"></i> অফারসমূহ</a></li>
                        <li><a href="/earning" class="nav-link font-semibold text-[0.95rem] hover:text-primary flex items-center gap-1.5 transition-colors"><i class="fa-solid fa-coins"></i> আর্ন জোন</a></li>
                        <li><a href="/digital-services" class="nav-link font-semibold text-[0.95rem] hover:text-primary flex items-center gap-1.5 transition-colors"><i class="fa-solid fa-laptop-code"></i> ডিজিটাল সার্ভিস</a></li>
                        <li><a href="/checkout" class="nav-link font-semibold text-[0.95rem] hover:text-primary flex items-center gap-1.5 transition-colors"><i class="fa-solid fa-cart-shopping text-primary"></i> কার্ট (<span id="cart-count">0</span>)</a></li>
                        <li><a href="/profile?tab=wishlist" class="nav-link font-semibold text-[0.95rem] hover:text-primary flex items-center gap-1.5 transition-colors"><i class="fa-solid fa-heart text-red-500"></i> পছন্দের তালিকা (<span id="fav-count">0</span>)</a></li>
                        
                        <li id="dynamic-nav" class="w-full lg:w-auto">
                            <a href="/login" class="block text-center font-semibold text-[0.95rem] bg-primary text-white py-2 px-5 rounded-full hover:bg-secondary transition-all shadow-md shadow-primary/10">লগইন</a>
                        </li>
                    </ul>
                </div>
            </header>
        `;

        // মোবাইল হ্যামবার্গার মেনু টগল অটো-বাইন্ডিং লজিক
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

    // খ. লাক্সারি ডার্ক থিম ফুটার রেন্ডারিং (সব পেজে সিঙ্ক থাকবে)
    if (footerPlaceholder) {
        footerPlaceholder.innerHTML = `
            <footer class="bg-[#0B0F19] text-gray-400 py-16 border-t border-white/5 font-bangla">
                <div class="max-w-[1200px] mx-auto px-5 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-12 mb-12">
                    <div class="footer-col">
                        <a href="/" class="font-headings font-extrabold text-3xl text-primary mb-5 inline-block">MartBaseBD</a>
                        <p class="text-[0.92rem] leading-relaxed mb-6 text-gray-400">
                            বাংলাদেশের সেরা প্রিমিয়াম রিসেলিং ও ওয়ার্ক প্ল্যাটফর্ম। আধুনিক উপায়ে কেনাকাটা এবং স্বনির্ভরতা অর্জনে আমরা সর্বদা আপনার পাশে আছি।
                        </p>
                        <div class="footer-socials flex gap-3">
                            <a href="https://facebook.com" class="w-9 h-9 bg-white/5 rounded-full flex items-center justify-center text-gray-300 hover:bg-primary hover:text-white hover:-translate-y-1 transition-all" target="_blank"><i class="fa-brands fa-facebook-f"></i></a>
                            <a href="https://youtube.com" class="w-9 h-9 bg-white/5 rounded-full flex items-center justify-center text-gray-300 hover:bg-primary hover:text-white hover:-translate-y-1 transition-all" target="_blank"><i class="fa-brands fa-youtube"></i></a>
                            <a href="https://telegram.org" class="w-9 h-9 bg-white/5 rounded-full flex items-center justify-center text-gray-300 hover:bg-primary hover:text-white hover:-translate-y-1 transition-all" target="_blank"><i class="fa-brands fa-telegram"></i></a>
                            <a href="https://whatsapp.com" class="w-9 h-9 bg-white/5 rounded-full flex items-center justify-center text-gray-300 hover:bg-primary hover:text-white hover:-translate-y-1 transition-all" target="_blank"><i class="fa-brands fa-whatsapp"></i></a>
                        </div>
                    </div>
                    <div class="footer-col">
                        <h4 class="text-white text-[1.15rem] font-bold mb-6 relative pb-2 after:content-[''] after:absolute after:bottom-0 after:left-0 after:w-6 after:h-[3px] after:bg-primary after:rounded-full">মেনু লিঙ্কসমূহ</h4>
                        <ul class="footer-links list-none text-sm space-y-3">
                            <li><a href="/" class="hover:text-primary hover:translate-x-1 transition-all inline-block"><i class="fa-solid fa-chevron-right text-[0.7rem] text-primary mr-1"></i> হোম</a></li>
                            <li><a href="/#products-section" class="hover:text-primary hover:translate-x-1 transition-all inline-block"><i class="fa-solid fa-chevron-right text-[0.7rem] text-primary mr-1"></i> প্রোডাক্টস</a></li>
                            <li><a href="/#offers-section" class="hover:text-primary hover:translate-x-1 transition-all inline-block"><i class="fa-solid fa-chevron-right text-[0.7rem] text-primary mr-1"></i> অফারসমূহ</a></li>
                            <li><a href="/earning" class="hover:text-primary hover:translate-x-1 transition-all inline-block"><i class="fa-solid fa-chevron-right text-[0.7rem] text-primary mr-1"></i> আর্ন জোন</a></li>
                            <li><a href="/digital-services" class="hover:text-primary hover:translate-x-1 transition-all inline-block"><i class="fa-solid fa-chevron-right text-[0.7rem] text-primary mr-1"></i> ডিজিটাল সার্ভিস</a></li>
                        </ul>
                    </div>
                    <div class="footer-col">
                        <h4 class="text-white text-[1.15rem] font-bold mb-6 relative pb-2 after:content-[''] after:absolute after:bottom-0 after:left-0 after:w-6 after:h-[3px] after:bg-primary after:rounded-full">পলিসি ও গাইডলাইন</h4>
                        <ul class="footer-links list-none text-sm space-y-3">
                            <li><a href="/about" class="hover:text-primary hover:translate-x-1 transition-all inline-block"><i class="fa-solid fa-chevron-right text-[0.7rem] text-primary mr-1"></i> আমাদের সম্পর্কে</a></li>
                            <li><a href="/contact" class="hover:text-primary hover:translate-x-1 transition-all inline-block"><i class="fa-solid fa-chevron-right text-[0.7rem] text-primary mr-1"></i> যোগাযোগ করুন</a></li>
                            <li><a href="/privacy" class="hover:text-primary hover:translate-x-1 transition-all inline-block"><i class="fa-solid fa-chevron-right text-[0.7rem] text-primary mr-1"></i> গোপনীয়তা নীতি</a></li>
                            <li><a href="/refund-policy" class="hover:text-primary hover:translate-x-1 transition-all inline-block"><i class="fa-solid fa-chevron-right text-[0.7rem] text-primary mr-1"></i> রিফান্ড পলিসি</a></li>
                            <li><a href="/reseller-policy" class="hover:text-primary hover:translate-x-1 transition-all inline-block"><i class="fa-solid fa-chevron-right text-[0.7rem] text-primary mr-1"></i> রিসেলার পলিসি</a></li>
                            <li><a href="/report" class="hover:text-primary hover:translate-x-1 transition-all inline-block"><i class="fa-solid fa-chevron-right text-[0.7rem] text-primary mr-1"></i> অভিযোগ ও রিপোর্ট</a></li>
                        </ul>
                    </div>
                    <div class="footer-col">
                        <h4 class="text-white text-[1.15rem] font-bold mb-6 relative pb-2 after:content-[''] after:absolute after:bottom-0 after:left-0 after:w-6 after:h-[3px] after:bg-primary after:rounded-full">পেমেন্ট মেথডস</h4>
                        <p class="text-sm leading-relaxed mb-4">নিরাপদ পেমেন্ট গেটওয়ের মাধ্যমে আপনার ট্রানজেকশন সম্পন্ন করুন নিশ্চিন্তে।</p>
                        <div class="payment-gateways flex flex-wrap gap-2">
                            <span class="gateway-badge bg-white/5 border border-white/10 px-3 py-1 rounded text-xs font-bold text-white">bKash</span>
                            <span class="gateway-badge bg-white/5 border border-white/10 px-3 py-1 rounded text-xs font-bold text-white">Nagad</span>
                            <span class="gateway-badge bg-white/5 border border-white/10 px-3 py-1 rounded text-xs font-bold text-white">Rocket</span>
                            <span class="gateway-badge bg-white/5 border border-white/10 px-3 py-1 rounded text-xs font-bold text-white font-body">Cards</span>
                        </div>
                    </div>
                </div>
                <div class="copyright-bar border-t border-white/5 pt-6 text-center text-sm text-gray-500">
                    <p>&copy; 2026 MartBaseBD Premium Work & Earn Platform. All rights reserved. | Developed by <a href="https://github.com/alihosen" class="text-primary hover:underline font-semibold" target="_blank">Ali Hosen</a></p>
                </div>
            </footer>
        `;
    }
}

// ৪. ডাইনামিক সেশন ভেরিফিকেশন ও নেভিগেশন লিংক আপডেট
async function updateLayoutNavigation() {
    const dynamicNav = document.getElementById('dynamic-nav');
    if (!supabaseClient || !dynamicNav) return;

    try {
        const { data: { session } } = await supabaseClient.auth.getSession();
        if (session) {
            // কাস্টমার লগইন থাকলে স্বয়ংক্রিয়ভাবে হিরো সেকশন হাইড হবে
            const heroSection = document.getElementById('hero-section');
            if (heroSection) heroSection.classList.add('hidden');

            const userId = session.user.id;
            const { data: profile } = await supabaseClient.from('profiles').select('role').eq('id', userId).single();
            
            if (profile) {
                if (profile.role === 'reseller') {
                    dynamicNav.outerHTML = `
                        <li><a href="/dashboard/reseller" class="nav-link font-semibold text-[0.95rem] hover:text-primary flex items-center gap-1.5 transition-colors"><i class="fa-solid fa-chart-line"></i> রিসেলার প্যানেল</a></li>
                        <li class="w-full lg:w-auto"><a href="#" onclick="handleLayoutLogout()" class="nav-link block text-center font-semibold text-[0.95rem] bg-primary text-white py-2 px-5 rounded-full hover:bg-secondary transition-all shadow-md shadow-primary/10"><i class="fa-solid fa-arrow-right-from-bracket"></i> লগআউট</a></li>
                    `;
                } else if (profile.role === 'admin') {
                    dynamicNav.outerHTML = `
                        <li><a href="/dashboard/admin" class="nav-link font-semibold text-[0.95rem] hover:text-primary flex items-center gap-1.5 transition-colors"><i class="fa-solid fa-chart-line"></i> এডমিন প্যানেল</a></li>
                        <li class="w-full lg:w-auto"><a href="#" onclick="handleLayoutLogout()" class="nav-link block text-center font-semibold text-[0.95rem] bg-primary text-white py-2 px-5 rounded-full hover:bg-secondary transition-all shadow-md shadow-primary/10"><i class="fa-solid fa-arrow-right-from-bracket"></i> লগআউট</a></li>
                    `;
                } else {
                    dynamicNav.outerHTML = `
                        <li><a href="/profile" class="nav-link font-semibold text-[0.95rem] hover:text-primary flex items-center gap-1.5 transition-colors"><i class="fa-solid fa-user-gear"></i> প্রোফাইল</a></li>
                        <li><a href="/checkout" class="nav-link font-semibold text-[0.95rem] hover:text-primary flex items-center gap-1.5 transition-colors"><i class="fa-solid fa-credit-card"></i> চেকআউট</a></li>
                        <li class="w-full lg:w-auto"><a href="#" onclick="handleLayoutLogout()" class="nav-link block text-center font-semibold text-[0.95rem] bg-primary text-white py-2 px-5 rounded-full hover:bg-secondary transition-all shadow-md shadow-primary/10"><i class="fa-solid fa-arrow-right-from-bracket"></i> লগআউট</a></li>
                    `;
                }
            }
        }
    } catch (e) {
        console.error("Layout auth routing error:", e);
    }
}

// ৫. গ্লোবাল লগআউট অ্যাকশন
window.handleLayoutLogout = async function() {
    if (supabaseClient) {
        await supabaseClient.auth.signOut();
        window.location.reload();
    }
}

// ৬. গ্লোবাল কার্ট ও উইশলিস্ট ব্যাজ আপডেট লজিক
window.updateLayoutBadges = function() {
    const cart = JSON.parse(localStorage.getItem('cart')) || [];
    const wishlist = JSON.parse(localStorage.getItem('wishlist')) || [];
    
    const cartCount = document.getElementById('cart-count');
    const favCount = document.getElementById('fav-count');
    
    if (cartCount) cartCount.innerText = cart.length;
    if (favCount) favCount.innerText = wishlist.length;
                                         }
