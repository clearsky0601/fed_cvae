import copy

from torch.optim import Adam

from models.VAE import CVAE
from users.user import User
from utils import one_hot_encode, reconstruction_loss, kl_divergence


class UserFedVAE(User):
    def __init__(self, base_params, z_dim, image_size, beta, pmf):
        super().__init__(base_params)

        self.z_dim = z_dim
        self.model = CVAE(
            num_classes=self.num_classes,
            num_channels=self.num_channels,
            z_dim=z_dim,
            image_size=image_size,
        )
        self.optimizer = Adam(self.model.parameters(), lr=0.001)

        self.beta = beta

        # Distribution of targets
        self.pmf = pmf

    def train(self, local_epochs):
        self.model.train()

        for epoch in range(local_epochs):
            for batch_idx, (X_batch, y_batch) in enumerate(self.dataloader):

                y_hot = one_hot_encode(y_batch, self.num_classes)

                X_recon, mu, logvar = self.model(X_batch, y_hot)

                # Calculate losses
                recon_loss = reconstruction_loss(self.num_channels, X_batch, X_recon)
                total_kld = kl_divergence(mu, logvar)
                total_loss = recon_loss + self.beta * total_kld

                # Update net params
                self.optimizer.zero_grad()
                total_loss.backward()
                self.optimizer.step()

    def update_decoder(self, decoder_state_dict):
        """Helper method to swap out the current decoder for a new decoder ensuring it is a new object with a deep copy."""

        self.model.decoder.load_state_dict(copy.deepcopy(decoder_state_dict))
