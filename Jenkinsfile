def group = 'datascience'
def project = 'redshift-unload'
def namespace = "${group}/${project}"

def imageName
def imageVersion

builderNode {
  stage("build and promote") {
    checkout scm
    imageVersion = lendupVersion()
    imageName = buildLendupDockerImage(artifactory: true, repository: namespace)

    promoteLendupDockerImage(artifactory: true, imageName: imageName, toTags: [imageVersion], registry: "docker-builds")

    if (BRANCH_NAME == "master") {
      promoteLendupDockerImage(artifactory: true, imageName: imageName, toTags: ["latest"], registry: "docker-builds")
      promoteLendupDockerImage(artifactory: true, imageName: imageName, toTags: [imageVersion, "latest"])
    }
  }
}
