/* Thème kibo, direction A « Carnet de terrain » : scripts légers, sans service tiers. */

/* Vidéos intégrées responsives */
(function () {
    var sources = [
        '.gh-content iframe[src*="youtube.com"]',
        '.gh-content iframe[src*="youtube-nocookie.com"]',
        '.gh-content iframe[src*="player.vimeo.com"]',
        '.gh-content object',
        '.gh-content embed'
    ];
    if (typeof reframe === 'function') reframe(document.querySelectorAll(sources.join(',')));
})();

/* Tableaux : défilement horizontal contenu dans leur boîte (aucun défilement de page à 360 px) */
(function () {
    document.querySelectorAll('.gh-content > table').forEach(function (table) {
        var wrapper = document.createElement('div');
        wrapper.className = 'gh-table';
        table.parentNode.insertBefore(wrapper, table);
        wrapper.appendChild(table);
    });
})();

/* Intertitres réels du contenu : repérage des sections Sources et « Pour aller plus loin » */
(function () {
    var content = document.querySelector('.kb-content');
    if (!content) return;

    function norm(text) {
        return (text || '').trim().toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '');
    }

    content.querySelectorAll(':scope > h2').forEach(function (h2) {
        var name = norm(h2.textContent);
        var cls = null;
        if (/^sources?$/.test(name)) cls = 'kb-sources';
        else if (/^pour aller plus loin/.test(name)) cls = 'kb-further';
        if (!cls) return;
        h2.setAttribute('data-kb-section', cls);
        for (var el = h2.nextElementSibling; el && !/^(H2|HR)$/.test(el.tagName); el = el.nextElementSibling) {
            if (/^(UL|OL)$/.test(el.tagName)) el.classList.add(cls);
        }
    });
})();

/* Paragraphe réduit à un tiret (marqueur d'import) : masqué à l'affichage, le contenu n'est pas modifié */
(function () {
    document.querySelectorAll('.kb-content > p').forEach(function (p) {
        if (/^[-\u2013\u2014]$/.test(p.textContent.trim())) p.classList.add('kb-stray');
    });
})();

/* Note « À propos de cette page » (citation commençant par ℹ️) : encart de carnet */
(function () {
    document.querySelectorAll('.kb-content > blockquote').forEach(function (q) {
        if (/^\s*\u2139/.test(q.textContent)) q.classList.add('kb-aside-note');
    });
})();

/* Sommaire : construit depuis les h2 réels, collant en marge sur bureau, repliable en tête sur téléphone */
(function () {
    var toc = document.querySelector('[data-kb-toc]');
    var content = document.querySelector('.kb-content');
    if (!toc || !content) return;

    var headings = Array.prototype.filter.call(content.querySelectorAll(':scope > h2'), function (h) {
        return h.textContent.trim().length > 0;
    });
    if (headings.length < 2) { toc.hidden = true; return; }

    var list = toc.querySelector('.kb-toc-list');
    var links = [];
    headings.forEach(function (h, i) {
        if (!h.id) h.id = 'section-' + (i + 1);
        h.setAttribute('tabindex', '-1');
        var li = document.createElement('li');
        var a = document.createElement('a');
        a.href = '#' + h.id;
        a.textContent = h.textContent.trim();
        li.appendChild(a);
        list.appendChild(li);
        links.push(a);
    });

    var summary = toc.querySelector('.kb-toc-summary .kb-label');
    if (summary) summary.textContent = 'Sommaire · ' + headings.length + ' parties';

    var details = toc.querySelector('details');
    var desktop = window.matchMedia('(min-width: 1024px)');
    function syncOpen() { details.open = desktop.matches; }
    syncOpen();
    desktop.addEventListener('change', syncOpen);
    details.querySelector('summary').addEventListener('click', function (e) {
        if (desktop.matches) e.preventDefault();
    });

    /* Sur téléphone, refermer le sommaire après un choix pour rendre la lecture */
    list.addEventListener('click', function () {
        if (!desktop.matches) details.open = false;
    });

    /* Repère de lecture (scrollspy) : aria-current suit l'intertitre visible */
    function setCurrent(id) {
        links.forEach(function (a) {
            a.setAttribute('aria-current', a.getAttribute('href') === '#' + id ? 'true' : 'false');
        });
    }

    var ticking = false;
    function update() {
        ticking = false;
        var current = '';
        for (var i = 0; i < headings.length; i++) {
            if (headings[i].getBoundingClientRect().top < window.innerHeight * 0.3) current = headings[i].id;
        }
        setCurrent(current);
    }
    window.addEventListener('scroll', function () {
        if (!ticking) { ticking = true; window.requestAnimationFrame(update); }
    }, {passive: true});
    update();
})();

/* Accroches en gras en tête de paragraphe : classe de repère (le contenu n'est pas modifié) */
(function () {
    document.querySelectorAll('.kb-content > p').forEach(function (p) {
        var first = p.firstChild;
        while (first && first.nodeType === 3 && !first.textContent.trim()) first = first.nextSibling;
        if (!first || first.nodeType !== 1 || !/^(STRONG|B)$/.test(first.tagName)) return;
        var t = first.textContent.trim();
        if (t.length < 8 || t.length > 120 || !/[.:?!]$/.test(t) || first === p.lastElementChild && !first.nextSibling) return;
        first.classList.add('kb-lead');
        p.classList.add('has-lead');
    });
})();

/* Sources annoncées en tête de page : lien vers la section Sources dans les métadonnées */
(function () {
    var cart = document.querySelector('[data-kb-cart-sources]');
    var meta = cart ? cart.querySelector('dd') : document.querySelector('.kb-article-head .kb-meta');
    var heading = document.querySelector('.kb-content > h2[data-kb-section="kb-sources"]');
    if (!meta || !heading) return;
    if (cart) cart.hidden = false;
    if (!heading.id) heading.id = 'sources';
    var n = 0;
    for (var el = heading.nextElementSibling; el && !/^(H2|HR)$/.test(el.tagName); el = el.nextElementSibling) {
        if (/^(UL|OL)$/.test(el.tagName)) n += el.children.length;
    }
    var span = document.createElement('span');
    var a = document.createElement('a');
    a.href = '#' + heading.id;
    a.textContent = cart ? (n ? n + ', en bas de page ↓' : 'En bas de page ↓') : (n ? n + (n > 1 ? ' sources' : ' source') : 'Sources') + ' en bas de page ↓';
    span.appendChild(a);
    meta.appendChild(span);
})();

/* Carnet vide (ni métadonnées ni sources) : classe posée une fois, au lieu d'un sélecteur :has() coûteux */
function kbNotesState() {
    document.querySelectorAll('.kb-reading').forEach(function (r) {
        var meta = r.querySelector('.kb-notes-meta');
        var src = r.querySelector('.kb-notes-sources');
        r.classList.toggle('kb-no-notes', !meta && (!src || src.hidden));
    });
}

/* Une seule occurrence d'abonnement : si le contenu porte sa carte d'inscription, le bloc du thème s'efface */
document.querySelectorAll('.kb-article').forEach(function (a) {
    if (a.querySelector('.gh-content .kg-signup-card')) a.classList.add('has-signup-card');
});

/* Carnet de notes : la liste des sources reprise dans la gouttière droite (bureau) */
(function () {
    var notes = document.querySelector('[data-kb-notes]');
    var content = document.querySelector('.kb-content');
    if (!notes || !content) { kbNotesState(); return; }

    var heading = content.querySelector(':scope > h2[data-kb-section="kb-sources"]');
    if (!heading) return;
    var source = null;
    for (var el = heading.nextElementSibling; el && !/^(H2|HR)$/.test(el.tagName); el = el.nextElementSibling) {
        if (/^(UL|OL)$/.test(el.tagName)) { source = el; break; }
    }
    if (!source) return;

    var clone = source.cloneNode(true);
    clone.removeAttribute('id');
    clone.classList.remove('kb-sources');
    clone.querySelectorAll('[id]').forEach(function (n) { n.removeAttribute('id'); });
    notes.querySelector('.kb-notes-body').appendChild(clone);
    var all = notes.querySelector('.kb-notes-all');
    if (heading.id) all.setAttribute('href', '#' + heading.id); else all.remove();
    notes.hidden = false;
})();
kbNotesState();

/* Carte d'inscription de l'éditeur : étiquette visible du champ, rythme écrit, identifiants uniques */
(function () {
    document.querySelectorAll('.gh-content .kg-signup-card').forEach(function (card, i) {
        var input = card.querySelector('.kg-signup-card-input');
        var fields = card.querySelector('.kg-signup-card-fields');
        if (!input || !fields || card.querySelector('.kb-form-label')) return;
        var id = 'kb-signup-email-' + (i + 1);
        input.id = id;
        input.setAttribute('autocomplete', 'email');
        var label = document.createElement('label');
        label.className = 'kb-form-label';
        label.setAttribute('for', id);
        label.textContent = 'Ton adresse e-mail';
        fields.parentNode.insertBefore(label, fields);

        var heading = card.querySelector('.kg-signup-card-heading');
        if (heading) {
            var kicker = document.createElement('p');
            kicker.className = 'kb-label';
            kicker.textContent = 'Newsletter hebdomadaire';
            heading.parentNode.insertBefore(kicker, heading);
        }
    });
})();

/* Pages Basecamp : place dans le chapitre, page précédente / suivante et trois pages suivantes */
(function () {
    var route = document.querySelector('[data-kb-route]');
    if (!route) return;
    var current = route.getAttribute('data-current');
    var items = Array.prototype.slice.call(route.querySelectorAll('.kb-route-list > li'));
    if (!items.length) return;

    var index = -1;
    items.forEach(function (li, i) {
        if (li.getAttribute('data-slug') === current) {
            index = i;
            li.classList.add('is-current');
            var a = li.querySelector('a');
            if (a) a.setAttribute('aria-current', 'page');
        }
    });

    var box = route.querySelector('[data-kb-next]');
    var list = route.querySelector('[data-kb-next-list]');
    var progress = route.querySelector('[data-kb-progress]');
    if (!box || !list) return;

    function entry(li, step) {
        var a = li.querySelector('a');
        var out = document.createElement('li');
        var link = document.createElement('a');
        link.href = a.href;
        var label = document.createElement('span');
        label.className = 'kb-label kb-next-step';
        label.textContent = step;
        var title = document.createElement('span');
        title.className = 'kb-next-title';
        title.textContent = a.textContent.trim();
        link.appendChild(label);
        link.appendChild(title);
        var excerpt = (li.getAttribute('data-excerpt') || '').trim();
        if (excerpt && excerpt !== '…') {
            var p = document.createElement('span');
            p.className = 'kb-next-excerpt';
            p.textContent = excerpt;
            link.appendChild(p);
        }
        out.appendChild(link);
        return out;
    }

    var n = items.length;
    /* Signature S3 : voie d'ascension à camps, deux camps avant et après la page, puis le sommet */
    function camp(li, i, step) {
        var e = entry(li, 'Camp ' + (i + 1) + (step ? ' · ' + step : ''));
        var ex = e.querySelector('.kb-next-excerpt');
        if (ex && step !== 'page suivante') ex.remove();
        return e;
    }
    if (index >= 0) {
        if (progress) progress.textContent = 'Page ' + (index + 1) + ' sur ' + n + ' dans ce chapitre (ordre alphabétique).';
        for (var b = Math.max(0, index - 2); b < index; b++) list.appendChild(camp(items[b], b, b === index - 1 ? 'page précédente' : ''));
        var here = document.createElement('li');
        here.className = 'is-current';
        var hereBox = document.createElement('div');
        hereBox.className = 'kb-next-current';
        hereBox.innerHTML = '<span class="kb-label kb-next-step">Camp ' + (index + 1) + ' · tu es ici</span>';
        var hereTitle = document.createElement('span');
        hereTitle.className = 'kb-next-title';
        hereTitle.textContent = items[index].textContent.trim();
        hereBox.appendChild(hereTitle);
        here.appendChild(hereBox);
        list.appendChild(here);
        for (var k = index + 1; k <= index + 2 && k < n; k++) list.appendChild(camp(items[k], k, k === index + 1 ? 'page suivante' : ''));
    } else {
        if (progress) progress.textContent = n + ' pages dans ce chapitre.';
        items.slice(0, 4).forEach(function (li, i) { list.appendChild(camp(li, i, '')); });
    }
    /* Sommet : lien vers la dernière page du chapitre, si elle n'est pas déjà parmi les camps */
    var reste = n - 1 - Math.min(n - 1, Math.max(index, 0) + 2);
    if (reste > 0) {
        var summit = entry(items[n - 1], 'Sommet · camp ' + n + ' · dernière page du chapitre');
        summit.className = 'is-summit';
        var sx = summit.querySelector('.kb-next-excerpt');
        if (sx) sx.remove();
        list.appendChild(summit);
    }
    box.hidden = false;
})();

/* Données structurées (schema.org) tirées du DOM visible, textes déjà décodés :
   BreadcrumbList depuis le fil d'Ariane, ItemList des chapitres sur le hub Basecamp.
   Le JSON-LD de Ghost (Article) reste intact ; ce bloc s'y ajoute. */
(function () {
    var canonical = document.querySelector('link[rel="canonical"]');
    var here = canonical ? canonical.href : location.href.split('#')[0];
    function clean(text) { return (text || '').replace(/\s+/g, ' ').trim(); }
    function emit(data) {
        var s = document.createElement('script');
        s.type = 'application/ld+json';
        s.setAttribute('data-kb-schema', data['@type']);
        s.textContent = JSON.stringify(data);
        document.head.appendChild(s);
    }
    var nav = document.querySelector('.kb-article-head .kb-crumbs');
    var crumbs = nav ? nav.querySelectorAll('li') : [];
    if (crumbs.length) {
        var items = [];
        crumbs.forEach(function (li) {
            var a = li.querySelector('a');
            var url = a ? a.href : here;
            if (items.length && items[items.length - 1].item === url) items.pop();
            items.push({ '@type': 'ListItem', position: items.length + 1, name: clean(li.textContent), item: url });
        });
        emit({ '@context': 'https://schema.org', '@type': 'BreadcrumbList', itemListElement: items });
    }
    var chapters = document.querySelectorAll('.kb-book-chapter-title a');
    if (chapters.length) {
        var list = [];
        chapters.forEach(function (a, i) {
            var name = a.querySelector('.kb-book-chapter-name');
            list.push({ '@type': 'ListItem', position: i + 1, name: clean((name || a).textContent), url: a.href });
        });
        emit({ '@context': 'https://schema.org', '@type': 'ItemList', name: 'Basecamp · table des matières', url: here, itemListElement: list });
    }
})();
