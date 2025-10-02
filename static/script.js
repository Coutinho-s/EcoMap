document.addEventListener('DOMContentLoaded', () => {

    // ================== CEP ==================
    const cepInput = document.getElementById('cep');
    if (cepInput) {
        cepInput.addEventListener('input', () => {
            let value = cepInput.value.replace(/\D/g, ''); // Remove não números
            if (value.length > 8) value = value.slice(0, 8); // Limita 8 dígitos
            if (value.length > 5) value = value.slice(0, 5) + '-' + value.slice(5); // Formato 00000-000
            cepInput.value = value;
        });
    }

    // ================== TAGS MATERIAIS ==================
    const materiaisInput = document.getElementById('materiais-input');
    const materiaisContainer = document.getElementById('materiais-tags');
    const materiaisHidden = document.getElementById('materiais_selecionados');

    let materiaisArray = materiaisHidden && materiaisHidden.value
        ? materiaisHidden.value.split(',')
        : [];

    function renderMateriais() {
        if (!materiaisContainer) return;
        materiaisContainer.innerHTML = '';
        materiaisArray.forEach((m, idx) => {
            const span = document.createElement('span');
            span.className = 'badge bg-success me-1 mb-1';
            span.style.cursor = 'pointer';
            span.title = 'Clique para remover';
            span.textContent = m;
            span.addEventListener('click', () => {
                materiaisArray.splice(idx, 1);
                renderMateriais();
            });
            materiaisContainer.appendChild(span);
        });
        if (materiaisHidden) materiaisHidden.value = materiaisArray.join(',');
    }

    renderMateriais();

    if (materiaisInput) {
        materiaisInput.addEventListener('keydown', e => {
            if (e.key === 'Enter') {
                e.preventDefault();
                const val = materiaisInput.value.trim();
                if (val) {
                    materiaisArray.push(val);
                    materiaisInput.value = '';
                    renderMateriais();
                }
            }
        });
    }

    // ================== DARK MODE ==================
    const toggleBtn = document.getElementById('dark-mode-toggle');
    if (toggleBtn) {
        toggleBtn.addEventListener('click', () => {
            const isDark = document.body.classList.toggle('dark-mode');
            toggleBtn.textContent = isDark ? '☀️' : '🌙';
            localStorage.setItem('ecoDarkMode', isDark);
        });

        if (localStorage.getItem('ecoDarkMode') === 'true') {
            document.body.classList.add('dark-mode');
            toggleBtn.textContent = '☀️';
        }
    }

    // ================== GOOGLE MAPS ==================
    const mapContainer = document.getElementById('map');
    if (mapContainer && typeof google !== 'undefined' && google.maps) {
        const map = new google.maps.Map(mapContainer, {
            center: { lat: -23.5505, lng: -46.6333 },
            zoom: 12
        });

        fetch('/api/pontos')
            .then(res => res.json())
            .then(data => {
                const bounds = new google.maps.LatLngBounds();
                data.forEach(p => {
                    const lat = parseFloat(p.latitude);
                    const lng = parseFloat(p.longitude);
                    if (!isNaN(lat) && !isNaN(lng)) {
                        const marker = new google.maps.Marker({
                            position: { lat, lng },
                            map: map,
                            title: p.nome
                        });

                        const infoWindow = new google.maps.InfoWindow({
                            content: `
                                <b>${p.nome}</b><br>
                                ${p.rua}, ${p.numero} ${p.complemento || ''}<br>
                                ${p.bairro}<br>
                                Horário: ${p.horarios_inicio} — ${p.horarios_fim}
                            `
                        });

                        marker.addListener('click', () => infoWindow.open(map, marker));
                        bounds.extend(marker.position);
                    }
                });

                if (!bounds.isEmpty()) map.fitBounds(bounds);
            })
            .catch(err => console.error("Erro ao carregar os pontos:", err));
    }

});
