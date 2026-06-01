---
name: angular-bootstrap
description: "ALWAYS use when working with Angular Bootstrap, ng-bootstrap, Bootstrap components in Angular, or Bootstrap 5 integration."
metadata:
  version: 17.0.0
  generated_by: oguzhancart
  generated_at: 2026-02-19
---

# ng-bootstrap / Angular Bootstrap

**Version:** ng-bootstrap 17.x (2025)
**Tags:** Bootstrap, UI Components, ng-bootstrap

**References:** [ng-bootstrap](https://ng-bootstrap.github.io/) • [GitHub](https://github.com/ng-bootstrap/ng-bootstrap)

## API Changes

This section documents recent version-specific API changes.

- NEW: Bootstrap 5 support — Full Bootstrap 5 integration

- NEW: Standalone components — All components are standalone

- NEW: Bootstrap icons support — Icon integration

- NEW: Angular 17+ support — Full compatibility with modern Angular

## Best Practices

- Install ng-bootstrap

```bash
npm install @ng-bootstrap/ng-bootstrap @popperjs/core bootstrap
```

- Import styles in angular.json

```json
{
  "styles": ["node_modules/bootstrap/dist/css/bootstrap.min.css"]
}
```

- Import NgbModule

```ts
import { NgbModule } from '@ng-bootstrap/ng-bootstrap';

@NgModule({
  imports: [NgbModule]
})
export class AppModule {}
```

- Use standalone import

```ts
import { NgbCarouselModule } from '@ng-bootstrap/ng-bootstrap';

@Component({
  standalone: true,
  imports: [NgbCarouselModule],
  // ...
})
export class CarouselComponent {}
```

- Use Modal

```ts
import { NgbModal } from '@ng-bootstrap/ng-bootstrap';

@Component({})
export class ModalComponent {
  constructor(private modalService: NgbModal) {}

  open(content: TemplateRef<any>) {
    this.modalService.open(content);
  }
}
```

- Use Dropdown

```ts
import { NgbDropdownModule } from '@ng-bootstrap/ng-bootstrap';

@Component({
  template: `
    <div ngbDropdown>
      <button ngbDropdownToggle>Menu</button>
      <div ngbDropdownMenu>
        <button ngbDropdownItem>Action</button>
      </div>
    </div>
  `
})
export class DropdownComponent {}
```

- Use Accordion

```ts
import { NgbAccordionModule } from '@ng-bootstrap/ng-bootstrap';

@Component({
  template: `
    <ngb-accordion>
      <ngb-panel title="First">
        <ng-template ngbPanelContent>Content 1</ng-template>
      </ngb-panel>
    </ngb-accordion>
  `
})
export class AccordionComponent {}
```

- Use Datepicker

```ts
import { NgbDatepickerModule } from '@ng-bootstrap/ng-bootstrap';

@Component({
  template: `
    <ngb-datepicker [(ngModel)]="date"></ngb-datepicker>
  `
})
export class DatePickerComponent {
  date: NgbDateStruct;
}
```

- Use Toast

```ts
import { NgbToast } from '@ng-bootstrap/ng-bootstrap';

@Component({
  template: `
    @for (toast of toasts; track toast) {
      <ngb-toast>{{ toast }}</ngb-toast>
    }
  `
})
export class ToastComponent {}
```

- Use Typeahead

```ts
import { NgbTypeaheadModule } from '@ng-bootstrap/ng-bootstrap';

@Component({
  template: `
    <input ngbTypeahead [ngModel]="value" [source]="search" />
  `
})
export class TypeaheadComponent {
  search = (text$: Observable<string>) => 
    text$.pipe(debounceTime(200), distinctUntilChanged());
}
```
