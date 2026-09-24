program i169d_atand_values
  implicit none
  integer, parameter :: RK = kind(0.0d0)
  real(kind=RK) :: y, x, observed, reference
  y = 1.0_RK
  x = 2.0_RK
  observed = atand(y, x)
  reference = atan2d(y, x)
  call require_true('atand two argument result matches atan2d', observed == reference)
  write(*,'(a)') 'INTRINSICS 16.9.D ATAND VALUES OK'
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
end program i169d_atand_values
