#include <rviz/visualization_frame.h>
#include <rviz/visualization_manager.h>
#include <rviz/render_panel.h>
#include <OgreRenderWindow.h>
#include <QPainter>
#include <QPixmap>
#include <QImage>
#include <string>

// Capture the live Qt controls and the OGRE framebuffer at the same callback.
// QWidget::grab alone cannot read WSLg's native OpenGL child surface.
extern "C" int capture_rviz(void* ptr, const char* path) {
  try {
    auto* frame = static_cast<rviz::VisualizationFrame*>(ptr);
    auto* panel = frame->getManager()->getRenderPanel();
    auto* window = panel->getRenderWindow();
    const std::string viewport_file = std::string(path) + ".viewport.png";
    QPixmap controls = frame->grab();
    window->update();
    window->writeContentsToFile(viewport_file);
    QImage viewport(QString::fromStdString(viewport_file));
    if (viewport.isNull()) return 2;
    QPainter painter(&controls);
    painter.drawImage(QRect(panel->mapTo(frame, QPoint(0, 0)), panel->size()), viewport);
    painter.end();
    return controls.save(QString::fromUtf8(path)) ? 0 : 3;
  } catch (...) { return 4; }
}
