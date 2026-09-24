program i169d_atan2_arguments
  implicit none
  integer, parameter :: RK = kind(0.0d0)
  real(kind=RK) :: arg_y, arg_x, high_y, high_x
  real(kind=RK) :: sign_result
  arg_y = 1.0_RK
  arg_x = 2.0_RK
  sign_result = atan2(arg_y, arg_x)
  call require_true('atan2 real y reaches positive radian branch', &
       sign_result > 0.0_RK .and. sign_result < 4.0_RK)
  high_y = 1.0_RK
  high_x = 2.0_RK
  call require_true('atan2 same kind operands keep x kind', &
       kind(atan2(high_y, high_x)) == kind(high_x))
  write(*,'(a)') 'INTRINSICS 16.9.D ATAN2 ARGUMENTS OK'
contains
  subroutine require_true(label, condition)
    character(len=*), intent(in) :: label
    logical, intent(in) :: condition
    if (.not. condition) then
      write(*,'(a)') label
      error stop
    end if
  end subroutine require_true
  subroutine require_complex_kind(label, value)
    character(len=*), intent(in) :: label
    complex(kind=kind(0.0d0)), intent(in) :: value
    call require_true(label, kind(value) == kind(0.0d0))
  end subroutine require_complex_kind
end program i169d_atan2_arguments
