(function(){
  const canvas = document.getElementById('cv');
  const healthEl = document.getElementById('health');
  const enemiesEl = document.getElementById('enemies');
  const scoreEl = document.getElementById('score');

  // Enhanced 3D Scene Setup
  const scene = new THREE.Scene();
  scene.fog = new THREE.Fog(0x0a1a2a, 10, 50);
  
  const camera = new THREE.PerspectiveCamera(75, window.innerWidth/window.innerHeight, 0.1, 100);
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  
  function resize(){
    const w = window.innerWidth, h = window.innerHeight;
    renderer.setSize(w, h, false);
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
  }
  window.addEventListener('resize', resize);
  resize();

  // Enhanced Lighting
  const dirLight = new THREE.DirectionalLight(0xffffff, 1.2);
  dirLight.position.set(5, 10, 5);
  dirLight.castShadow = true;
  scene.add(dirLight);
  const ambLight = new THREE.AmbientLight(0x404060, 0.4);
  scene.add(ambLight);

  // Enhanced Arena
  const ARENA_SIZE = 20;
  const arenaGeometry = new THREE.PlaneGeometry(ARENA_SIZE, ARENA_SIZE);
  const arenaMaterial = new THREE.MeshLambertMaterial({ color: 0x0a3a44 });
  const arena = new THREE.Mesh(arenaGeometry, arenaMaterial);
  arena.rotation.x = -Math.PI/2;
  arena.receiveShadow = true;
  scene.add(arena);
  
  // Enhanced Player
  const playerGeometry = new THREE.SphereGeometry(0.5, 32, 32);
  const playerMaterial = new THREE.MeshPhongMaterial({ color: 0x4ecdc4, shininess: 100 });
  const player = new THREE.Mesh(playerGeometry, playerMaterial);
  player.position.set(0, 0.5, 0);
  player.castShadow = true;
  scene.add(player);

  // Enhanced Camera System
  const cameraOffset = new THREE.Vector3(0, 6, 8);
  camera.position.set(player.position.x + cameraOffset.x, player.position.y + cameraOffset.y, player.position.z + cameraOffset.z);
  camera.lookAt(player.position);

  // Enemy System
  const enemies = [];
  const enemyPool = [];
  const MAX_ENEMIES = 15;
  const TARGET_ENEMIES = 8;

  function createEnemy() {
    let enemy;
    if (enemyPool.length > 0) {
      enemy = enemyPool.pop();
      enemy.visible = true;
    } else {
      const geometry = new THREE.BoxGeometry(0.8, 0.8, 0.8);
      const material = new THREE.MeshPhongMaterial({ color: 0xff6b6b });
      enemy = new THREE.Mesh(geometry, material);
      enemy.castShadow = true;
      scene.add(enemy);
    }
    const side = Math.floor(Math.random() * 4);
    const offset = ARENA_SIZE * 0.4;
    switch(side) {
      case 0: enemy.position.set((Math.random() - 0.5) * offset, 0.4, -offset); break;
      case 1: enemy.position.set((Math.random() - 0.5) * offset, 0.4, offset); break;
      case 2: enemy.position.set(offset, 0.4, (Math.random() - 0.5) * offset); break;
      case 3: enemy.position.set(-offset, 0.4, (Math.random() - 0.5) * offset); break;
    }
    enemy.userData = { speed: 0.02 + Math.random() * 0.02, health: 1, lastHit: 0 };
    enemies.push(enemy);
    return enemy;
  }

  function removeEnemy(enemy, index) {
    enemies.splice(index, 1);
    enemy.visible = false;
    enemyPool.push(enemy);
  }

  for(let i = 0; i < TARGET_ENEMIES; i++) createEnemy();

  // Game State
  let health = 100;
  let score = 0;
  let gameOver = false;
  let gameTime = 0;
  let spawnTimer = 0;
  let totalBulletsFired = 0;

  // Controls
  const keys = {};
  document.addEventListener('keydown', e => { keys[e.code] = true; if (e.code === 'Space') shoot(); });
  document.addEventListener('keyup', e => keys[e.code] = false);

  // Shooting System
  const bullets = [];
  const bulletPool = [];

  function shoot() {
    if (gameOver) return;
    let bullet;
    if (bulletPool.length > 0) {
      bullet = bulletPool.pop();
      bullet.visible = true;
    } else {
      const geometry = new THREE.SphereGeometry(0.1, 8, 8);
      const material = new THREE.MeshBasicMaterial({ color: 0xffff00 });
      bullet = new THREE.Mesh(geometry, material);
      scene.add(bullet);
    }
    bullet.position.copy(player.position);
    const direction = new THREE.Vector3(0, 0, -1).applyQuaternion(camera.quaternion);
    bullet.userData = { direction, speed: 0.5, life: 60 };
    bullets.push(bullet);
    totalBulletsFired++;
  }

  // **** MODIFIED WebSocket Connection ****
  let ws = null;
  const proto = location.protocol === 'https:' ? 'wss' : 'ws';
  
  function connectWebSocket() {
    // Connect to the main AURA backend game endpoint
    ws = new WebSocket(`${proto}://${location.host}/ws/game`);
    ws.onopen = () => console.log('Game WebSocket connected to AURA');
    ws.onclose = () => {
      console.log('Game WebSocket disconnected, retrying...');
      setTimeout(connectWebSocket, 2000);
    };
    ws.onmessage = (e) => {
      try {
        const msg = JSON.parse(e.data);
        if (msg.type === 'aura_instruction') {
          // Future: adapt visuals / audio playback. For now log.
          console.log('AURA instruction', msg.payload);
        }
      } catch {}
    };
  }
  
  connectWebSocket();

  // **** MODIFIED Game State Reporting ****
  let lastPos = player.position.clone();
  let lastSendTime = 0;
  
  function sendGameState() {
    if (!ws || ws.readyState !== 1) return;
    const now = performance.now();
    if (now - lastSendTime < 200) return; // Throttle to 5fps
    
    const delta = player.position.clone().sub(lastPos);
    const speedMetric = Math.min(1, delta.length() * 4);
    lastPos.copy(player.position);
    
    let nearestDist = Infinity;
    enemies.forEach(enemy => {
      const dist = enemy.position.distanceTo(player.position);
      if (dist < nearestDist) nearestDist = dist;
    });
    const proximity = Math.max(0, Math.min(1, 1 - (nearestDist / 10)));
    
    // This structure MUST match the Pydantic model in the backend
    const gameState = {
      player_health: health,
      enemy_count: enemies.length,
      score: score,
      player_speed: speedMetric,
      threat_proximity: proximity,
      game_time: Math.floor(gameTime / 60),
      bullets_fired: totalBulletsFired
    };
    
    ws.send(JSON.stringify({
      type: 'game_state',
      payload: gameState
    }));
    
    lastSendTime = now;
  }

  // Collision Detection
  function checkCollisions() {
    const playerBox = new THREE.Box3().setFromObject(player);
    enemies.forEach((enemy, index) => {
      const enemyBox = new THREE.Box3().setFromObject(enemy);
      if (playerBox.intersectsBox(enemyBox)) {
        health = Math.max(0, health - 1);
        if (health <= 0 && !gameOver) gameOver = true;
      }
    });
    bullets.forEach((bullet, bulletIndex) => {
      const bulletBox = new THREE.Box3().setFromObject(bullet);
      enemies.forEach((enemy, enemyIndex) => {
        if (!enemy.visible || !bullet.visible) return;
        const enemyBox = new THREE.Box3().setFromObject(enemy);
        if (bulletBox.intersectsBox(enemyBox)) {
          bullets.splice(bulletIndex, 1); bullet.visible = false; bulletPool.push(bullet);
          score += 50;
          removeEnemy(enemy, enemyIndex);
          if (enemies.length < TARGET_ENEMIES) createEnemy();
        }
      });
    });
  }

  // Boundary Collision
  function checkBoundaries() {
    const halfArena = ARENA_SIZE / 2 - 0.5;
    player.position.x = Math.max(-halfArena, Math.min(halfArena, player.position.x));
    player.position.z = Math.max(-halfArena, Math.min(halfArena, player.position.z));
  }

  // Main Game Loop
  function gameLoop() {
    if (gameOver) { requestAnimationFrame(gameLoop); return; }
    
    gameTime++;
    const moveSpeed = 0.1;
    if (keys['KeyW']) player.position.z -= moveSpeed;
    if (keys['KeyS']) player.position.z += moveSpeed;
    if (keys['KeyA']) player.position.x -= moveSpeed;
    if (keys['KeyD']) player.position.x += moveSpeed;
    
    checkBoundaries();
    camera.position.set(player.position.x, 6, player.position.z + 8);
    camera.lookAt(player.position);
    
    enemies.forEach(enemy => {
      const direction = player.position.clone().sub(enemy.position).normalize();
      enemy.position.addScaledVector(direction, enemy.userData.speed);
    });
    
    bullets.forEach((bullet, index) => {
      bullet.position.addScaledVector(bullet.userData.direction, bullet.userData.speed);
      bullet.userData.life--;
      if (bullet.userData.life <= 0) {
        bullets.splice(index, 1); bullet.visible = false; bulletPool.push(bullet);
      }
    });
    
    spawnTimer++;
    if (spawnTimer > 180 && enemies.length < MAX_ENEMIES) {
      createEnemy();
      spawnTimer = 0;
    }
    
    checkCollisions();
    healthEl.textContent = health;
    enemiesEl.textContent = enemies.length;
    scoreEl.textContent = score;
    
    sendGameState();
    
    renderer.render(scene, camera);
    requestAnimationFrame(gameLoop);
  }
  
  gameLoop();
})();