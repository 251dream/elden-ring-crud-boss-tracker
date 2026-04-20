// auto-hide flash messages after delay
document.querySelectorAll('.flash').forEach(flash => {
  setTimeout(() => {
    flash.style.transition = 'opacity .4s ease, transform .4s ease';
    flash.style.opacity = '0';
    flash.style.transform = 'translateY(-4px)';
    setTimeout(() => flash.remove(), 400);
  }, 4000);
});

// toggle sidebar state (mobile vs desktop)
function toggleSidebar(){
  if (window.innerWidth <= 768){
    document.getElementById('sidebar')?.classList.toggle('mobile-open');
  } else {
    document.body.classList.toggle('sidebar-collapsed');
    localStorage.setItem('sc', document.body.classList.contains('sidebar-collapsed') ? '1' : '0');
  }
  updateLegendPosition();
}

// restore sidebar collapsed state on load (desktop only)
if (localStorage.getItem('sc') === '1' && window.innerWidth > 768)
  document.body.classList.add('sidebar-collapsed');

// attach toggle handlers to buttons
document.getElementById('sidebarToggle')?.addEventListener('click', toggleSidebar);
document.getElementById('topbarToggle')?.addEventListener('click', toggleSidebar);

// close mobile sidebar when clicking outside
document.addEventListener('click', e => {
  const sb = document.getElementById('sidebar');
  if (window.innerWidth <= 768 && sb?.classList.contains('mobile-open') &&
      !sb.contains(e.target) && !document.getElementById('topbarToggle')?.contains(e.target)){
    sb.classList.remove('mobile-open');
    updateLegendPosition();
  }
});

// keep map legend aligned with map column
function updateLegendPosition(){
  const legend = document.getElementById('mapLegendFixed');
  const col = document.getElementById('dashMapCol');
  if (!legend || !col) return;
  legend.style.left = (col.getBoundingClientRect().left + 12) + 'px';
}

// update legend on window resize
window.addEventListener('resize', updateLegendPosition);

// run after DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  setTimeout(updateLegendPosition, 80);

  // animate difficulty bars (grow width)
  document.querySelectorAll('.diff-fill, .diff-fill-lg').forEach((bar, i) => {
    const w = bar.style.width;
    bar.style.width = '0';
    setTimeout(() => {
      bar.style.transition = 'width .55s ease';
      bar.style.width = w;
    }, 60 + i * 40);
  });

  // fade + slide in cards and rows
  document.querySelectorAll('.stat-card, .bsl-item, .boss-row, .boss-card-mobile').forEach((el, i) => {
    el.style.opacity = '0';
    el.style.transform = 'translateY(7px)';
    setTimeout(() => {
      el.style.transition = 'opacity .3s ease, transform .3s ease';
      el.style.opacity = '';
      el.style.transform = '';
    }, 50 + i * 25);
  });

  // animated counters for stats
  document.querySelectorAll('[data-count]').forEach(el => {
    const target = parseInt(el.dataset.count, 10); // final value
    if (!target) return;
    let cur = 0;
    const step = Math.max(1, Math.ceil(target / 22)); // increment step
    const t = setInterval(() => {
      cur = Math.min(cur + step, target); // increase toward target
      el.textContent = cur;
      if (cur >= target) clearInterval(t); // stop when done
    }, 26);
  });
});

// confirm delete action
function confirmDelete(name){
  return confirm('Remove "' + name + '" from tracker?\n\nThis cannot be undone.');
}
