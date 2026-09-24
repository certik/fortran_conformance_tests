program i169d_atan2_values
  implicit none
  integer, parameter :: RK = kind(0.0d0)
  real(kind=RK) :: pos_value, zero_value, neg_value
  real(kind=RK) :: y_pos, y_neg, y_zero, x_pos, x_neg
  y_pos = 1.0_RK
  y_neg = -1.0_RK
  y_zero = 0.0_RK
  x_pos = 2.0_RK
  x_neg = -2.0_RK
  pos_value = atan2(y_pos, x_neg)
  call require_true('atan2 positive y gives positive result', pos_value > 0.0_RK)
  zero_value = atan2(y_zero, x_pos)
  call require_true('atan2 zero y positive x result is y', zero_value == y_zero)
  neg_value = atan2(y_neg, x_pos)
  call require_true('atan2 negative y gives negative result', neg_value < 0.0_RK)
  write(*,'(a)') 'INTRINSICS 16.9.D ATAN2 VALUES OK'
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
end program i169d_atan2_values
