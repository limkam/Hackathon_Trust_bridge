const { registerStartup } = require('../scripts/registerStartup');
const { issueCertificate } = require('../scripts/issueCertificate');

describe('Startup Registry Tests', () => {
    let startupId;
    const mockFounderAddress = 'FB7xNwme7h5VZxTMa26jmGQqfz4dJGrsaGDx1ZRbfX5t'; // Valid Solana address format

    test('should register a startup successfully', async () => {
        const result = await registerStartup({
            startupName: 'AgriTech SL',
            sector: 'Agriculture Technology',
            founderAddress: mockFounderAddress,
        });

        expect(result).toHaveProperty('startupId');
        expect(result).toHaveProperty('transactionSignature');
        expect(result).toHaveProperty('blockchainProof');

        startupId = result.startupId;

        expect(result.startupId).toContain('STARTUP-');
        expect(result.transactionSignature).toBeTruthy();
    }, 30000);

    test('should register multiple startups', async () => {
        const startups = [
            {
                startupName: 'FinTech Solutions SL',
                sector: 'Financial Technology',
                founderAddress: mockFounderAddress,
            },
            {
                startupName: 'EduTech Innovations',
                sector: 'Education Technology',
                founderAddress: mockFounderAddress,
            },
        ];

        const results = await Promise.all(
            startups.map(startup => registerStartup(startup))
        );

        expect(results).toHaveLength(2);
        results.forEach(result => {
            expect(result).toHaveProperty('startupId');
            expect(result).toHaveProperty('transactionSignature');
        });
    }, 60000);
});

