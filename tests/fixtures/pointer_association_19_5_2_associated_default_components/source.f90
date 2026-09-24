! rule: S19.5.2.3-001
! covers: default-initialized-component-intent-out-associated default-initialized-component-unsaved-local-associated default-initialized-component-block-local-associated default-initialized-component-allocated-associated
! evidence: effect
! standard: f2023
! oracle-basis: standard
module pa1952_default_assoc_m
  implicit none
  integer, target, save :: default_target = 401, other_target = 409
  type :: box_intent
    integer, pointer :: p => default_target
  end type
  type :: box_local
    integer, pointer :: p => default_target
  end type
  type :: box_block
    integer, pointer :: p => default_target
  end type
  type :: box_alloc
    integer, pointer :: p => default_target
  end type
contains
  subroutine intent_out_event(box)
    type(box_intent), intent(out) :: box
  end subroutine
  subroutine local_event(ok, value)
    logical, intent(out) :: ok
    integer, intent(out) :: value
    type(box_local) :: local
    ok = associated(local%p, default_target)
    value = local%p
  end subroutine
  subroutine block_event(ok, value)
    logical, intent(out) :: ok
    integer, intent(out) :: value
    block
      type(box_block) :: local
      ok = associated(local%p, default_target)
      value = local%p
    end block
  end subroutine
end module pa1952_default_assoc_m
program pa1952_associated_default_components
  use pa1952_default_assoc_m
  implicit none
  type(box_intent) :: intent_box
  type(box_alloc), allocatable :: allocated_box
  logical :: ok
  integer :: value, checks
  checks = 0
  intent_box%p => other_target
  call intent_out_event(intent_box)
  call expect_true(associated(intent_box%p, default_target), 'INTENT(OUT) non-NULL default component')
  call expect_equal(intent_box%p, 401, 'INTENT(OUT) non-NULL default value')
  call local_event(ok, value)
  call expect_true(ok, 'unsaved local non-NULL default component')
  call expect_equal(value, 401, 'unsaved local non-NULL default value')
  call block_event(ok, value)
  call expect_true(ok, 'BLOCK local non-NULL default component')
  call expect_equal(value, 401, 'BLOCK local non-NULL default value')
  allocate(box_alloc :: allocated_box)
  call expect_true(associated(allocated_box%p, default_target), 'allocated non-NULL default component')
  call expect_equal(allocated_box%p, 401, 'allocated non-NULL default value')
  call expect_equal(checks, 8, 'check count before completion')
  write(*,'(a)') 'POINTER ASSOCIATION 19.5.2 ASSOCIATED DEFAULT COMPONENTS OK'
contains
  subroutine expect_true(observed, label)
    logical, intent(in) :: observed
    character(len=*), intent(in) :: label
    if (.not. observed) then
      write(*,'(a,1x,a)') 'PA1952-FAIL', label
      error stop
    end if
    checks = checks + 1
  end subroutine
  subroutine expect_false(observed, label)
    logical, intent(in) :: observed
    character(len=*), intent(in) :: label
    if (observed) then
      write(*,'(a,1x,a)') 'PA1952-FAIL', label
      error stop
    end if
    checks = checks + 1
  end subroutine
  subroutine expect_equal(observed, expected, label)
    integer, intent(in) :: observed, expected
    character(len=*), intent(in) :: label
    if (observed /= expected) then
      write(*,'(a,1x,a,1x,i0,1x,i0)') 'PA1952-FAIL', label, observed, expected
      error stop
    end if
    checks = checks + 1
  end subroutine
end program pa1952_associated_default_components
