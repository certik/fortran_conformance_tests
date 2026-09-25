! rule: S15.5.2.5-007
! covers: allocatable-inquiry-exception
! evidence: effect
! standard: f2023
module ordinary_dummy_core_m
  implicit none
  integer, parameter :: k4 = selected_int_kind(4)
  type :: parent
    integer :: base = -1
  end type
  type, extends(parent) :: child
    integer :: ext = -2
  end type
  integer, pointer :: module_p => null(), module_q => null()
contains
  subroutine observe_scope(x, out)
    integer, intent(in) :: x
    integer, intent(out) :: out
    out = x
  end subroutine
  subroutine observe_class(x, out_base, out_ext)
    class(parent), intent(in) :: x
    integer, intent(out) :: out_base, out_ext
    select type (x)
    type is (child)
      out_base = x%base
      out_ext = x%ext
    class default
      out_base = x%base
      out_ext = -777
    end select
  end subroutine
  subroutine observe_poly_assumed_size(x, out_ext)
    class(parent), intent(in) :: x(*)
    integer, intent(out) :: out_ext
    select type (x)
    type is (child)
      out_ext = x(1)%ext
    class default
      out_ext = -778
    end select
  end subroutine
  subroutine observe_kind(x, out_kind, out_value)
    integer(kind=k4), intent(in) :: x
    integer, intent(out) :: out_kind, out_value
    out_kind = kind(x)
    out_value = int(x)
  end subroutine
  subroutine observe_char_scalar(x, out_len, out_text)
    character(len=3), intent(inout) :: x
    integer, intent(out) :: out_len
    character(len=3), intent(out) :: out_text
    out_len = len(x)
    out_text = x
    x = 'XYZ'
  end subroutine
  subroutine observe_char_array(x, seen)
    character(len=1), intent(inout) :: x(4)
    character(len=4), intent(out) :: seen
    seen = x(1) // x(2) // x(3) // x(4)
    x(3) = 'Q'
  end subroutine
  subroutine observe_assumed_char(x, out_len, out_last)
    character(len=*), intent(in) :: x
    integer, intent(out) :: out_len
    character(len=1), intent(out) :: out_last
    out_len = len(x)
    out_last = x(len(x):len(x))
  end subroutine
  subroutine read_allocated(x, out)
    integer, allocatable, intent(in) :: x
    integer, intent(out) :: out
    out = x
  end subroutine
  subroutine observe_target(x, inside_assoc, inside_value)
    integer, target, intent(inout) :: x
    logical, intent(out) :: inside_assoc
    integer, intent(out) :: inside_value
    inside_assoc = associated(module_p, x)
    inside_value = x
    module_q => x
  end subroutine
  subroutine observe_scalar_rule(x, out)
    integer, intent(in) :: x
    integer, intent(out) :: out
    out = x
  end subroutine
end module
program ordinary_dummy_core
  use ordinary_dummy_core_m
  implicit none
  integer :: checks = 0, out = -91, out_kind = -92, out_len = -93
  integer(kind=k4) :: kind_actual = 123_k4
  type(child) :: child_actual, poly_array(2)
  character(len=5) :: char_actual = 'ABCDE'
  character(len=3) :: char_text = '###'
  character(len=2) :: char_matrix(3) = ['AB', 'CD', 'EF']
  character(len=4) :: seq_seen = '####'
  character(len=7) :: long_char = 'ABCDEFG'
  character(len=1) :: last_char = '#'
  integer, allocatable :: allocated_value, not_allocated
  logical :: flag = .false.
  integer, target :: target_value = 79
  call observe_scope(31, out)
  call expect_equal(out, 31, 'ordinary dummy scope scalar')
  child_actual%base = 11; child_actual%ext = 13
  call observe_class(child_actual, out, out_kind)
  call expect_equal(out, 11, 'type compatible parent part')
  call expect_equal(out_kind, 13, 'type compatible extension part')
  poly_array(1)%base = 21; poly_array(1)%ext = 44
  call observe_poly_assumed_size(poly_array, out)
  call expect_equal(out, 44, 'polymorphic assumed-size actual')
  call observe_kind(kind_actual, out_kind, out)
  call expect_equal(out_kind, k4, 'kind parameter agreement kind')
  call expect_equal(out, 123, 'kind parameter agreement value')
  call observe_char_scalar(char_actual, out_len, char_text)
  call expect_equal(out_len, 3, 'scalar character dummy length')
  call expect_char3(char_text, 'ABC', 'default character length exception')
  call expect_char5(char_actual, 'XYZDE', 'scalar leftmost definition')
  call observe_char_array(char_matrix, seq_seen)
  call expect_char4(seq_seen, 'ABCD', 'array character leftmost sequence')
  call expect_char2(char_matrix(2), 'QD', 'array character definition')
  call observe_assumed_char(long_char, out_len, last_char)
  call expect_equal(out_len, 7, 'assumed character length')
  call expect_char1(last_char, 'G', 'assumed character last')
  allocate(allocated_value); allocated_value = 67
  call read_allocated(allocated_value, out)
  call expect_equal(out, 67, 'allocated allocatable actual')
  flag = .true.
  flag = allocated(not_allocated)
  call expect_false(flag, 'allocatable inquiry exception')
  module_p => target_value
  flag = .false.; out = -94
  call observe_target(target_value, flag, out)
  call expect_true(flag, 'target dummy invocation association')
  call expect_equal(out, 79, 'target dummy invocation value')
  call expect_true(associated(module_q, target_value), 'target dummy return association')
  call expect_equal(module_q, 79, 'target dummy return value')
  call observe_scalar_rule(73, out)
  call expect_equal(out, 73, 'nonelemental scalar dummy scalar actual')
  call expect_equal(checks, 20, 'check count')
  write(*,'(a)') 'ORDINARY DUMMY CORE OK'
contains
  subroutine expect_equal(got, want, label)
    integer, intent(in) :: got, want
    character(len=*), intent(in) :: label
    if (got /= want) then
      write(*,'(a,1x,a,1x,i0,1x,i0)') 'OD15525-FAIL', label, got, want
      error stop
    end if
    checks = checks + 1
  end subroutine
  subroutine expect_true(got, label)
    logical, intent(in) :: got
    character(len=*), intent(in) :: label
    if (.not. got) then
      write(*,'(a,1x,a)') 'OD15525-FAIL', label
      error stop
    end if
    checks = checks + 1
  end subroutine
  subroutine expect_false(got, label)
    logical, intent(in) :: got
    character(len=*), intent(in) :: label
    if (got) then
      write(*,'(a,1x,a)') 'OD15525-FAIL', label
      error stop
    end if
    checks = checks + 1
  end subroutine
  subroutine expect_char1(got, want, label)
    character(len=1), intent(in) :: got, want
    character(len=*), intent(in) :: label
    if (len(got) /= 1 .or. got /= want) error stop label
    checks = checks + 1
  end subroutine
  subroutine expect_char2(got, want, label)
    character(len=2), intent(in) :: got, want
    character(len=*), intent(in) :: label
    if (len(got) /= 2 .or. got /= want) error stop label
    checks = checks + 1
  end subroutine
  subroutine expect_char3(got, want, label)
    character(len=3), intent(in) :: got, want
    character(len=*), intent(in) :: label
    if (len(got) /= 3 .or. got /= want) error stop label
    checks = checks + 1
  end subroutine
  subroutine expect_char4(got, want, label)
    character(len=4), intent(in) :: got, want
    character(len=*), intent(in) :: label
    if (len(got) /= 4 .or. got /= want) error stop label
    checks = checks + 1
  end subroutine
  subroutine expect_char5(got, want, label)
    character(len=5), intent(in) :: got, want
    character(len=*), intent(in) :: label
    if (len(got) /= 5 .or. got /= want) error stop label
    checks = checks + 1
  end subroutine
end program
