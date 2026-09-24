program i169d_atanh_complex_range
  implicit none
  integer, parameter :: RK = kind(0.0d0)
  complex(kind=RK) :: x, y
  real(kind=RK) :: imag_part
  x = cmplx(0.0_RK, 2.0_RK, kind=RK)
  y = atanh(x)
  imag_part = aimag(y)
  call require_true('atanh complex imaginary part lies in enclosing radian range', &
       imag_part >= -1.6_RK .and. imag_part <= 1.6_RK)
  write(*,'(a)') 'INTRINSICS 16.9.D ATANH COMPLEX RANGE OK'
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
end program i169d_atanh_complex_range
