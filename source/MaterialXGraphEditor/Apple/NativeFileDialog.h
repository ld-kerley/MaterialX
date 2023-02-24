//
// Copyright Contributors to the MaterialX Project
// SPDX-License-Identifier: Apache-2.0
//

#pragma once

#include <MaterialXGraphEditor/UiNode.h>
#include <filesystem>
#include <imfilebrowser.h>

namespace ed = ax::NodeEditor;
namespace mx = MaterialX;

// A class to substitute the Imgui file browser with a native implementation.
// Implements just the class methods used in the GraphEditor to reduce code divergence
class NativeFileDialog
{
  public:
    NativeFileDialog(ImGuiFileBrowserFlags flags = 0);
    void SetTitle(std::string title);
    void SetTypeFilters(const std::vector<std::string>& typeFilters);
    void Open();
    bool IsOpened();
    void Display();
    bool HasSelected();
    std::filesystem::path GetSelected();
    void ClearSelected();

  private:
    ImGuiFileBrowserFlags flags_;
    std::string title_;
    std::vector<std::string> typeFilters_;
    bool openFlag_ = false;
    bool isOpened_ = false;
    std::set<std::filesystem::path> selectedFilenames_;
};