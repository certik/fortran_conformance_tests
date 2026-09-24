program ieee_exception_arrays_status
  use, intrinsic :: ieee_arithmetic
  implicit none
  integer :: checks
  real :: sample
  type(ieee_modes_type) :: modes
  type(ieee_status_type) :: status
  logical :: observed
  checks = 0
  sample = 0.0
  call accept_modes(modes)
  call ieee_get_status(status)
  call accept_status(status)
  call prepare(ieee_overflow)
  call ieee_set_flag(ieee_overflow, .true.)
  call ieee_get_status(status)
  call ieee_set_flag(ieee_overflow, .false.)
  call ieee_set_status(status)
  call ieee_get_flag(ieee_overflow, observed)
  call expect_true(observed, 'status-restores-overflow')
  call assert_sets_flag(ieee_overflow, ieee_overflow, 'flag-overflow')
  call assert_sets_flag(ieee_divide_by_zero, ieee_divide_by_zero, 'flag-divide')
  call assert_sets_flag(ieee_invalid, ieee_invalid, 'flag-invalid')
  call assert_sets_flag(ieee_underflow, ieee_underflow, 'flag-underflow')
  call assert_sets_flag(ieee_inexact, ieee_inexact, 'flag-inexact')
  call assert_sets_flag(ieee_usual(1), ieee_overflow, 'usual-overflow')
  call assert_sets_flag(ieee_usual(2), ieee_divide_by_zero, 'usual-divide')
  call assert_sets_flag(ieee_usual(3), ieee_invalid, 'usual-invalid')
  call assert_sets_flag(ieee_all(1), ieee_overflow, 'all-overflow')
  call assert_sets_flag(ieee_all(2), ieee_divide_by_zero, 'all-divide')
  call assert_sets_flag(ieee_all(3), ieee_invalid, 'all-invalid')
  call assert_sets_flag(ieee_all(4), ieee_underflow, 'all-underflow')
  call assert_sets_flag(ieee_all(5), ieee_inexact, 'all-inexact')
  call expect_count(16)
  write(*,'(a)') 'IEEE 17.1-17.3 EXCEPTION ARRAYS STATUS SUPPORTED OK'
contains
  subroutine accept_modes(value)
    type(ieee_modes_type), intent(in) :: value
    checks = checks + 1
  end subroutine accept_modes
  subroutine accept_status(value)
    type(ieee_status_type), intent(in) :: value
    checks = checks + 1
  end subroutine accept_status
  subroutine expect_true(value, label)
    logical, intent(in) :: value
    character(len=*), intent(in) :: label
    if (.not. value) then
      write(*,'(a,1x,a)') 'IEEE17:true', label
      error stop 1
    end if
    checks = checks + 1
  end subroutine expect_true
  subroutine assert_sets_flag(setter, expected, label)
    type(ieee_flag_type), intent(in) :: setter, expected
    character(len=*), intent(in) :: label
    logical :: observed
    call prepare(expected)
    call ieee_set_flag(setter, .true.)
    call ieee_get_flag(expected, observed)
    if (.not. observed) then
      write(*,'(a,1x,a)') 'IEEE17:flag-array', label
      error stop 1
    end if
    call ieee_set_flag(expected, .false.)
    checks = checks + 1
  end subroutine assert_sets_flag
  subroutine prepare(flag)
    type(ieee_flag_type), intent(in) :: flag
    logical :: halting
    if (.not. ieee_support_flag(flag, sample)) error stop 77
    if (ieee_support_halting(flag)) then
      call ieee_set_halting_mode(flag, .false.)
    else
      call ieee_get_halting_mode(flag, halting)
      if (halting) error stop 77
    end if
    call ieee_set_flag(flag, .false.)
  end subroutine prepare
  subroutine expect_count(expected)
    integer, intent(in) :: expected
    if (checks /= expected) then
      write(*,'(a)') 'IEEE17:array-count'
      error stop 1
    end if
  end subroutine expect_count
end program ieee_exception_arrays_status
