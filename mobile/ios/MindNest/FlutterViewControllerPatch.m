// Workaround for https://github.com/flutter/flutter/issues/179422
//
// On iOS 26 with ProMotion displays (iPhone 17 Pro etc.), Flutter's
// -[FlutterViewController createTouchRateCorrectionVSyncClientIfNeeded]
// passes a nil task runner to VSyncClient, crashing at:
//   VSyncClient initWithTaskRunner:callback: + 300
//
// The method accesses the engine's C++ Shell before it has been fully
// initialized, which only manifests on iOS 26 due to the new
// _performDeferredInitialWindowUpdateForConnection lifecycle.
//
// This patch replaces the method with a no-op on iOS 26+.
// Touch rate correction (ProMotion touch synchronization) is skipped,
// which has no functional impact — only a minor rendering quality effect.
// Remove this file once Flutter releases a fix.

#import <Foundation/Foundation.h>
#import <objc/runtime.h>

@interface FlutterViewControllerPatch : NSObject
@end

@implementation FlutterViewControllerPatch

+ (void)load {
    if (@available(iOS 26.0, *)) {
        static dispatch_once_t onceToken;
        dispatch_once(&onceToken, ^{
            Class cls = NSClassFromString(@"FlutterViewController");
            if (!cls) return;

            SEL sel = NSSelectorFromString(@"createTouchRateCorrectionVSyncClientIfNeeded");
            Method method = class_getInstanceMethod(cls, sel);
            if (!method) return;

            IMP noopIMP = imp_implementationWithBlock(^(__unused id self) {
                // no-op: avoid nil task runner crash on iOS 26 (flutter#179422)
            });
            method_setImplementation(method, noopIMP);
        });
    }
}

@end
