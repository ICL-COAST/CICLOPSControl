using System;
using System.Windows.Forms;
using System.Threading;
using ASCOM.DeviceInterface;
using ASCOM.DriverAccess;

namespace TelescopeCircleMotion
{
    public partial class MainForm : Form
    {
        private Telescope telescope;
        private System.Threading.Timer motionTimer;
        private DateTime startTime;
        
        // Circle parameters
        private double centerAz = 180.0;     // Center azimuth in degrees (South)
        private double centerAlt = 45.0;     // Center altitude in degrees
        private double circleRadius = 10.0;  // Circle radius in degrees
        private double periodSeconds = 120;  // Time to complete one circle in seconds
        
        // Control parameters
        private const double Kp = 0.1;       // Proportional gain for feedback control
        
        public MainForm()
        {
            InitializeComponent();
        }

        private void btnConnect_Click(object sender, EventArgs e)
        {
            try
            {
                // Create the telescope instance - OmniSimulator
                telescope = new Telescope("ASCOM.Simulator.Telescope");
                
                // Connect to the telescope
                telescope.Connected = true;
                
                // Check if the telescope supports Az-Alt coordinates
                if (!telescope.CanSlewAltAz)
                {
                    MessageBox.Show("This telescope doesn't support Alt-Az slewing!");
                    telescope.Connected = false;
                    return;
                }
                
                // Set tracking off (we'll control motion directly)
                telescope.Tracking = false;
                
                // Start the motion timer
                startTime = DateTime.UtcNow;
                motionTimer = new System.Threading.Timer(ControlLoop, null, 0, 100); // 100ms update rate
                
                lblStatus.Text = "Connected and moving in circle!";
            }
            catch (Exception ex)
