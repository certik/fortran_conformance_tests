! rule: S19.5.2.4-001
! covers: source-allocate-disassociated-pointer-subobject default-null-component-intent-out-disassociated default-null-component-unsaved-local-disassociated default-null-component-block-local-disassociated default-null-component-allocated-disassociated
! evidence: effect
! standard: f2023
! oracle-basis: standard
program pa1952_disassociated_source_default
  implicit none
  type :: source_box
    integer, pointer :: p
  end type
  type :: box_intent
    integer, pointer :: p => null()
  end type
  type :: box_local
    integer, pointer :: p => null()
  end type
  type :: box_block
    integer, pointer :: p => null()
  end type
  type :: box_alloc
    integer, pointer :: p => null()
  end type
  integer, target :: target = 607
  type(source_box) :: src
  type(source_box), allocatable :: dst
  type(box_intent) :: intent_box
  type(box_alloc), allocatable :: allocated_box
  type(box_alloc) :: source_assoc
  integer :: checks
  checks = 0
  nullify(src%p)
  allocate(dst, source=src)
  call expect_false(associated(dst%p), 'SOURCE disassociated pointer subobject')
  intent_box%p => target
  call intent_out_event(intent_box)
  call expect_false(associated(intent_box%p), 'INTENT(OUT) NULL default component')
  call local_event()
  call local_event()
  call block_event()
  call block_event()
  source_assoc%p => target
  allocate(box_alloc :: allocated_box)
  call expect_false(associated(allocated_box%p), 'allocated NULL default component')
  call expect_equal(checks, 7, 'check count before completion')
  write(*,'(a)') 'POINTER ASSOCIATION 19.5.2 DISASSOCIATED SOURCE DEFAULT OK'
contains
  subroutine intent_out_event(box)
    type(box_intent), intent(out) :: box
  end subroutine
  subroutine local_event()
    type(box_local) :: local
    call expect_false(associated(local%p), 'unsaved local NULL default component')
    local%p => target
  end subroutine
  subroutine block_event()
    block
      type(box_block) :: local
      call expect_false(associated(local%p), 'BLOCK local NULL default component')
      local%p => target
    end block
  end subroutine
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
end program pa1952_disassociated_source_default
