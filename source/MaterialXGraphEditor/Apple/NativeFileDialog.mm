//
// Copyright Contributors to the MaterialX Project
// SPDX-License-Identifier: Apache-2.0
//

#include "NativeFileDialog.h"
#import <Cocoa/Cocoa.h>

NativeFileDialog::NativeFileDialog(ImGuiFileBrowserFlags flags) :
    flags_(flags)
{
}

void NativeFileDialog::SetTitle(std::string title)
{
    title_ = title;
}

void NativeFileDialog::SetTypeFilters(const std::vector<std::string>& typeFilters)
{
    typeFilters_ = typeFilters;
}

void NativeFileDialog::Open()
{
    ClearSelected();
    openFlag_ = true;
}

bool NativeFileDialog::IsOpened()
{
    return isOpened_;
}

void NativeFileDialog::Display()
{
    // Only call the dialog if it's not already displayed
    if (!openFlag_ || isOpened_)
    {
        return;
    }
    openFlag_ = false;

    // Check if we want to save or open
    bool save = !(flags_ & ImGuiFileBrowserFlags_SelectDirectory) &&
                (flags_ & ImGuiFileBrowserFlags_EnterNewFilename);

    // Create the type filter in a way that the NSFileDialogs can understand them
    NSMutableArray* types = [NSMutableArray new];
    for (auto& tf : typeFilters_)
    {
        NSString* typeFilter = [NSString stringWithUTF8String:tf.c_str()];
        // Imgui likes the extensions to start with a ., but Cocoa adds them
        // So we strip the first char.
        typeFilter = [typeFilter substringFromIndex:1];
        [types addObject:typeFilter];
    }

    if (save)
    {
        NSSavePanel* saveDlg = [NSSavePanel savePanel];
        saveDlg.title = [NSString stringWithUTF8String: title_.c_str()];

        [saveDlg setAllowedFileTypes:types];
        if ([saveDlg runModal] == NSModalResponseOK)
        {
            auto path = std::filesystem::path([[[saveDlg URL] path] UTF8String]);
            selectedFilenames_.insert(path);
        }
    }
    else
    {
        NSOpenPanel* openDlg = [NSOpenPanel openPanel];
        openDlg.title = [NSString stringWithUTF8String: title_.c_str()];

        [openDlg setCanChooseFiles:YES];
        [openDlg setCanChooseDirectories:NO];
        [openDlg setAllowedFileTypes:types];
        if ([openDlg runModal] == NSModalResponseOK)
        {
            for (NSURL* url in [openDlg URLs])
            {
                auto path = std::filesystem::path([[url path] UTF8String]);
                selectedFilenames_.insert(path);
            }
        }
    }

    isOpened_ = false;
}

bool NativeFileDialog::HasSelected()
{
    return !selectedFilenames_.empty();
}

std::filesystem::path NativeFileDialog::GetSelected()
{
    if (selectedFilenames_.empty())
    {
        return {};
    }

    return *selectedFilenames_.begin();
}

void NativeFileDialog::ClearSelected()
{
    selectedFilenames_.clear();
}