import brevitas.onnx as bo
import torchvision
from pathlib import Path
import torchvision
import torchvision.transforms as transforms
import torch
import torch.nn as nn
import torch.optim as optim
from cnn_model import makeCnnModel
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
current_dir = Path(__file__).parent
model = makeCnnModel().to(DEVICE)

criterion = nn.CrossEntropyLoss().to(DEVICE) # MNIST의 60000개의 training data로 cnn을 학습시키고, 10000개의 test set을 넣어 정확도 계산.
transform = transforms.Compose([transforms.ToTensor(), transforms.Normalize((0.5,), (0.5,))])

trainset = torchvision.datasets.MNIST(root=current_dir.joinpath('data'), train=True, download=True, transform=transform)
trainloader = torch.utils.data.DataLoader(trainset, batch_size=4, shuffle=True)

testset = torchvision.datasets.MNIST(root=current_dir.joinpath('data'), train=False, download=True, transform=transform)
testloader = torch.utils.data.DataLoader(testset, batch_size=4, shuffle=False)
optimizer = optim.SGD(model.parameters(), lr=0.001, momentum=0.9)

model_state = Path(__file__).parent.joinpath("state_dict_self-trained.pth")
if model_state.is_file():
    model = model.cpu()
    model.load_state_dict(torch.load(model_state))
    model = model.to(DEVICE)
    model.eval()
else:
    for epoch in range(3):  # 예제로 3 에폭만 학습, 실제로 epoch은 0,1,2
        model.train()
        running_loss = 0.0
        for i, data in enumerate(trainloader, 0):  # 미니배치 단위로 훈련 데이터셋 반복, 미니배치의 개수(i)=데이터셋 크기(60000)/배치 크기(4)
            inputs, labels = data
            inputs = inputs.to(DEVICE)
            labels = labels.to(DEVICE)
            # 텐서를 바이트 스트림으로 변환하는 부분. 추후 고려
            # with io,BytesIO() as output:
            #   torch.save(inputs, output)
            #   binary_data = output.getvalue()

            optimizer.zero_grad()  # 기울기 초기화
            outputs = model(inputs)  # 순전파
            loss = criterion(outputs, labels)  # 손실 계산
            loss.backward()  # 역전파
            optimizer.step()  # 가중치 업데이트
            running_loss += loss.item()  # 손실 누적
        print(f'Epoch {epoch + 1}, Loss: {running_loss / len(trainloader)}')
    model.eval()
    torch.save(model.state_dict(), "state_dict_self-trained.pth")

model.eval()
correct = 0
total = 0
with torch.no_grad(): # 기울기 계산 비활성화, 위에서 학습할 때는 기울기 계산 필요하지만, 테스트할 때는 필요없음
    for data in testloader: # 미니배치 순회
        images, labels = data
        images = images.to(DEVICE)
        labels = labels.to(DEVICE)
        outputs = model(images) # 순전파 수행
        _, predicted = torch.max(outputs.data, 1) # 모델의 출력 중 최댓값을 갖는 클래스의 인덱스를 예측값으로 선택
        total += labels.size(0) # 전체 샘플 수 업데이트
        correct += (predicted == labels).sum().item() # 올바르게 예측된 샘플 수 업데이트

print(f'Accuracy on the test dataset: {100 * correct / total}%')

dummy_input = torch.randn(1, 1, 28, 28, device=DEVICE) # 해당 입력이 28*28 tensor로 설정되어있음 (MNIST 형식 따라감)
onnx_filename = "brevitas_cnn.onnx" # 생성될 onnx파일 이름 설정, 사용자 마음대로 변경가능

onnx_path = current_dir.joinpath(onnx_filename) # onnx파일이 저장될 경로 설정, 수정 필요
bo.export_brevitas_onnx(model, dummy_input, onnx_path)


if __name__ == "__main__":
    pass


