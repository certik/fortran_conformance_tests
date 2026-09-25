! rule: S15.5.2.8-004
! covers: intent-in-dummy-pointer-associated-with-target-actual
! evidence: effect
! standard: f2023
module alloc_pointer_dummy_m
  implicit none
  type :: parent
    integer :: base = -1
  end type
  type, extends(parent) :: child
    integer :: ext = -2
  end type
  integer, pointer :: observed_ptr(:) => null()
  integer, pointer :: module_p(:) => null()
  integer, target :: module_target_scalar = 42
contains
  subroutine alloc_scope(x, out)
    integer, allocatable, intent(in) :: x
    integer, intent(out) :: out
    out = x
  end subroutine
  subroutine ptr_scope(p, out)
    integer, pointer, intent(in) :: p
    integer, intent(out) :: out
    out = p
  end subroutine
  subroutine class_ptr(p, out)
    class(parent), pointer, intent(in) :: p
    integer, intent(out) :: out
    select type (p)
    type is (child)
      out = p%ext
    class default
      out = -700
    end select
  end subroutine
  subroutine unlimited_alloc(x, out)
    class(*), allocatable, intent(in) :: x
    integer, intent(out) :: out
    select type (x)
    type is (integer)
      out = x
    class default
      out = -701
    end select
  end subroutine
  subroutine base_alloc(x, out)
    type(parent), allocatable, intent(in) :: x
    integer, intent(out) :: out
    out = x%base
  end subroutine
  subroutine rank_alloc(x, lo, hi, value)
    integer, allocatable, intent(in) :: x(:)
    integer, intent(out) :: lo, hi, value
    lo = lbound(x, 1)
    hi = ubound(x, 1)
    value = x(0)
  end subroutine
  subroutine fixed_char(x, out_len, out_text)
    character(len=2), allocatable, intent(in) :: x
    integer, intent(out) :: out_len
    character(len=2), intent(out) :: out_text
    out_len = len(x)
    out_text = x
  end subroutine
  subroutine assumed_char(p, out_len, out_ch)
    character(len=*), pointer, intent(in) :: p
    integer, intent(out) :: out_len
    character(len=1), intent(out) :: out_ch
    out_len = len(p)
    out_ch = p(3:3)
  end subroutine
  subroutine deferred_char(x, out_len, out_text)
    character(len=:), allocatable, intent(in) :: x
    integer, intent(out) :: out_len
    character(len=2), intent(out) :: out_text
    out_len = len(x)
    out_text = x
  end subroutine
  subroutine unallocated_inout(x, was_alloc)
    integer, allocatable, intent(inout) :: x
    logical, intent(out) :: was_alloc
    was_alloc = allocated(x)
    allocate(x)
    x = 42
  end subroutine
  subroutine intent_out_entry(x, was_alloc, lo, hi, value)
    integer, allocatable, intent(out) :: x(:)
    logical, intent(out) :: was_alloc
    integer, intent(out) :: lo, hi, value
    was_alloc = allocated(x)
    allocate(x(1:1))
    x(1) = 42
    lo = lbound(x, 1)
    hi = ubound(x, 1)
    value = x(1)
  end subroutine
  subroutine target_assoc(x, inside_assoc, inside_value)
    integer, allocatable, target, intent(inout) :: x(:)
    logical, intent(out) :: inside_assoc
    integer, intent(out) :: inside_value
    inside_assoc = associated(module_p, x)
    inside_value = x(0)
    observed_ptr => x
  end subroutine
  subroutine ptr_inout(q, is_assoc, value)
    integer, pointer, intent(inout) :: q
    logical, intent(out) :: is_assoc
    integer, intent(out) :: value
    is_assoc = associated(q)
    value = q
  end subroutine
  subroutine ptr_intent_in(q, is_assoc, value)
    integer, pointer, intent(in) :: q
    logical, intent(out) :: is_assoc
    integer, intent(out) :: value
    is_assoc = associated(q)
    value = q
  end subroutine
  subroutine ptr_target_in(q, is_assoc, value)
    integer, pointer, intent(in) :: q
    logical, intent(out) :: is_assoc
    integer, intent(out) :: value
    is_assoc = associated(q, module_target_scalar)
    value = q
  end subroutine
end module
program allocatable_pointer_dummy_effects
  use alloc_pointer_dummy_m
  implicit none
  integer :: checks = 0, out = -99, lo = -11, hi = -12, value = -13, len_value = -1
  logical :: flag = .true.
  character(len=2), allocatable :: ca
  character(len=:), allocatable :: cd
  character(len=2) :: text = '##'
  character(len=1) :: ch = '#'
  character(len=3), target :: char_target = 'abc'
  character(len=3), pointer :: char_pointer
  integer, allocatable, target :: array_actual(:)
  integer, allocatable :: scalar_alloc, unalloc, out_array(:)
  integer, target :: scalar_target = 43
  integer, pointer :: scalar_pointer, target_pointer
  type(child), target :: child_target
  class(parent), pointer :: poly_pointer
  class(*), allocatable :: any_alloc
  type(parent), allocatable :: base_actual
  allocate(scalar_alloc); scalar_alloc = 31
  call alloc_scope(scalar_alloc, out); call expect_equal(out, 31, 'allocatable same attribute scope')
  scalar_pointer => scalar_target
  call ptr_scope(scalar_pointer, out); call expect_equal(out, 43, 'pointer same attribute scope')
  child_target%base = 5; child_target%ext = 42; poly_pointer => child_target
  call class_ptr(poly_pointer, out); call expect_equal(out, 42, 'polymorphic pointer correspondence')
  allocate(any_alloc, source=42)
  call unlimited_alloc(any_alloc, out); call expect_equal(out, 42, 'unlimited polymorphic allocatable')
  allocate(base_actual); base_actual%base = 42
  call base_alloc(base_actual, out); call expect_equal(out, 42, 'declared type same allocatable')
  allocate(array_actual(-1:1)); array_actual = [40, 41, 42]
  call rank_alloc(array_actual, lo, hi, value)
  call expect_equal(lo, -1, 'allocatable rank lower bound')
  call expect_equal(hi, 1, 'allocatable rank upper bound')
  call expect_equal(value, 41, 'allocatable rank value')
  allocate(character(len=2) :: ca); ca = '42'
  call fixed_char(ca, len_value, text)
  call expect_equal(len_value, 2, 'fixed character length')
  call expect_char2(text, '42', 'fixed character text')
  char_pointer => char_target
  call assumed_char(char_pointer, len_value, ch)
  call expect_equal(len_value, 3, 'assumed character length')
  call expect_char1(ch, 'c', 'assumed character third')
  allocate(character(len=2) :: cd); cd = '42'
  call deferred_char(cd, len_value, text)
  call expect_equal(len_value, 2, 'deferred character length')
  call expect_char2(text, '42', 'deferred character text')
  if (allocated(unalloc)) error stop 91
  flag = .true.; call unallocated_inout(unalloc, flag)
  call expect_false(flag, 'unallocated actual passes in')
  call expect_true(allocated(unalloc), 'allocation status passes out')
  call expect_equal(unalloc, 42, 'allocated value passes out')
  allocate(out_array(-2:0)); out_array = [17, 18, 19]
  flag = .true.; call intent_out_entry(out_array, flag, lo, hi, value)
  call expect_false(flag, 'intent out deallocated on entry')
  call expect_equal(lo, 1, 'intent out new lower bound')
  call expect_equal(hi, 1, 'intent out new upper bound')
  call expect_equal(value, 42, 'intent out new value')
  deallocate(array_actual); allocate(array_actual(-1:1)); array_actual = [40, 41, 42]; module_p => array_actual
  flag = .false.; call target_assoc(array_actual, flag, value)
  call expect_true(flag, 'target dummy invocation pointer association')
  call expect_equal(value, 41, 'target dummy invocation value')
  call expect_true(associated(observed_ptr, array_actual), 'target dummy completion pointer association')
  call expect_equal(observed_ptr(0), 41, 'target dummy completion value')
  scalar_pointer => scalar_target
  flag = .false.; value = -42; call ptr_inout(scalar_pointer, flag, value)
  call expect_true(flag, 'non-intent-in pointer actual required')
  call expect_equal(value, 43, 'non-intent-in pointer value')
  target_pointer => module_target_scalar
  flag = .false.; value = -41; call ptr_intent_in(target_pointer, flag, value)
  call expect_true(flag, 'intent in pointer actual accepted')
  call expect_equal(value, 42, 'intent in pointer actual value')
  flag = .false.; value = -42; call ptr_target_in(module_target_scalar, flag, value)
  call expect_true(flag, 'intent in target actual associated')
  call expect_equal(value, 42, 'intent in target actual value')
  call expect_equal(checks, 31, 'check count')
  write(*,'(a)') 'ALLOCATABLE POINTER DUMMY EFFECTS OK'
contains
  subroutine expect_equal(got, want, label)
    integer, intent(in) :: got, want
    character(len=*), intent(in) :: label
    if (got /= want) then
      write(*,'(a,1x,a,1x,i0,1x,i0)') 'AA1552-FAIL', label, got, want
      error stop
    end if
    checks = checks + 1
  end subroutine
  subroutine expect_true(got, label)
    logical, intent(in) :: got
    character(len=*), intent(in) :: label
    if (.not. got) then
      write(*,'(a,1x,a)') 'AA1552-FAIL', label
      error stop
    end if
    checks = checks + 1
  end subroutine
  subroutine expect_false(got, label)
    logical, intent(in) :: got
    character(len=*), intent(in) :: label
    if (got) then
      write(*,'(a,1x,a)') 'AA1552-FAIL', label
      error stop
    end if
    checks = checks + 1
  end subroutine
  subroutine expect_char2(got, want, label)
    character(len=2), intent(in) :: got, want
    character(len=*), intent(in) :: label
    if (len(got) /= 2 .or. got /= want) then
      write(*,'(a,1x,a)') 'AA1552-FAIL', label
      error stop
    end if
    checks = checks + 1
  end subroutine
  subroutine expect_char1(got, want, label)
    character(len=1), intent(in) :: got, want
    character(len=*), intent(in) :: label
    if (len(got) /= 1 .or. got /= want) then
      write(*,'(a,1x,a)') 'AA1552-FAIL', label
      error stop
    end if
    checks = checks + 1
  end subroutine
end program
