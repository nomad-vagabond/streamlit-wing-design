var camera, scene, renderer, container;
var frustumSize = 400;

THREE.Cache.enabled = false;


function get_material(color, render_type) {

  let materials = {
    "shaded": new THREE.MeshPhongMaterial({
      color: color,
      specular: 1,
      shininess: 10,
    }),
    "transparent": new THREE.MeshPhongMaterial({
      color: color,
      specular: 1,
      shininess: 10,
      transparent: true,
      opacity: 0.5
    }),
    "wireframe": new THREE.MeshBasicMaterial({
      color: color,
      wireframe: true, 
      wireframeLinewidth: 40 
    })
  };

  return materials[render_type];

}

function onWindowResize() {
    renderer.setSize(container.clientWidth, container.clientHeight);
    camera.aspect = container.clientWidth / container.clientHeight;
    camera.updateProjectionMatrix();
}


class STLViewer extends HTMLElement {
  constructor() {
    super();
  }

  connectedCallback() {
    this.connected = true;
    let viewer = this;

    const shadowRoot = this.attachShadow({ mode: 'open' });
    container = document.createElement('div');
    container.style.width = '100%';
    container.style.height = '100%';

    shadowRoot.appendChild(container);

    const models = {__MODELS__};

    renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(container.clientWidth, container.clientHeight);
    container.appendChild(renderer.domElement);

    scene = new THREE.Scene();
    scene.add(new THREE.HemisphereLight(0xffffff,0x222222,0.8));
    scene.add(new THREE.AmbientLight(0x404040));

    let loader = new THREE.STLLoader();
    
    async function loadModels() {

        let meshes = [],
            lines = [],
            bbox = {
                "xmin": 0, "xmax": 0,
                "ymin": 0, "ymax": 0,
                "zmin": 0, "zmax": 0
            };

        for (let i in models) {
            let model_path = "./" + models[i]["path"] + "?cache=" + models[i]["time"]
            await loader.loadAsync(model_path).then(( geometry ) => {
                if (models[i]["rendr_type"] === "hidden") { return; }

                let material = get_material(models[i]["color"], models[i]["rendr_type"]);
                let mesh = new THREE.Mesh(geometry, material);
                scene.add(mesh);
                meshes.push(mesh);

                let edges = new THREE.EdgesGeometry(geometry, 29); 
                let line = new THREE.LineSegments(edges, new THREE.LineBasicMaterial( { color: "#555555" } ) ); 
                scene.add(line);
                lines.push(line);

                geometry.computeBoundingBox();

                bbox.xmin = Math.min(geometry.boundingBox.min.x, bbox.xmin);
                bbox.xmax = Math.max(geometry.boundingBox.max.x, bbox.xmax);

                bbox.ymin = Math.min(geometry.boundingBox.min.y, bbox.ymin);
                bbox.ymax = Math.max(geometry.boundingBox.max.y, bbox.ymax);

                bbox.zmin = Math.min(geometry.boundingBox.min.z, bbox.zmin);
                bbox.zmax = Math.max(geometry.boundingBox.max.z, bbox.zmax);
            });
        }

        bbox.center = new THREE.Vector3(
            (bbox.xmin + bbox.xmax) / 2.0,
            (bbox.ymin + bbox.ymax) / 2.0,
            (bbox.zmin + bbox.zmax) / 2.0,
        )

        bbox.xsize = bbox.xmax - bbox.xmin,
        bbox.ysize = bbox.ymax - bbox.ymin,
        bbox.zsize = bbox.zmax - bbox.zmin;

        // shift all objects to the common center
        for (let i in meshes) {
            meshes[i].geometry.applyMatrix4(new THREE.Matrix4().makeTranslation(-bbox.center.x, -bbox.center.y, -bbox.center.z));
            lines[i].geometry.applyMatrix4(new THREE.Matrix4().makeTranslation(-bbox.center.x, -bbox.center.y, -bbox.center.z));
        }

        return bbox;
    }

    loadModels().then((bbox) => {
        let bbox_max_size = Math.max(bbox.ysize, bbox.xsize, bbox.zsize);

        camera = new THREE.PerspectiveCamera(
            35, container.clientWidth / container.clientHeight, 
            0.1, bbox_max_size*4
        );

        camera.position.x = -bbox_max_size*0.5;
        camera.position.y = bbox_max_size*0.5;
        camera.position.z = bbox_max_size*1.2;

        camera.lookAt(new THREE.Vector3(0,0,0));
    
        let controls = new THREE.OrbitControls(camera, renderer.domElement);
        controls.enableZoom = true;
    
        window.addEventListener('resize', onWindowResize, false);
        controls.autoRotate = true;
        controls.autoRotateSpeed = -0.5;
    
        let animate = () => {
          controls.update();
          renderer.render(scene, camera);
          if (viewer.connected) {
            requestAnimationFrame(animate);
          }
        };
        animate();
    });

  }

  disconnectedCallback() {
    this.connected = false;
  }
}

customElements.define('stl-viewer', STLViewer);
