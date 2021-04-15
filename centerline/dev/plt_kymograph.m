%%
M=csvread('second_der_np_new.csv')';
%M=csvread('x_new_np.csv')';

figure;
imagesc(M)
colormap(paper_colormap);
colorbar;
k=0.02
% k=500
% caxis([100 500])
caxis([-k k]);

%%
xticklabels = 0:2.5:66;
xticks = linspace(1, size(M, 2), numel(xticklabels));
set(gca, 'XTick', xticks, 'XTickLabel', xticklabels, 'Fontsize', 20)
xlabel('Time (s)')
ylabel('Segment Curvature')


%%
xlim([8000 11000])
%%
set(gca, 'Fontsize', 20)



