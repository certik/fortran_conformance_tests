program i169d_atanh_arguments
  implicit none
  integer, parameter :: RK = kind(0.0d0)
  real(kind=RK) :: real_x, real_result
  complex(kind=RK) :: complex_x, complex_result
  real_x = 0.25_RK
  complex_x = cmplx(0.0_RK, 2.0_RK, kind=RK)
  real_result = atanh(real_x)
  complex_result = atanh(complex_x)
  call require_true('atanh real argument keeps real kind', kind(real_result) == kind(real_x))
  call require_true('atanh complex argument keeps complex kind', kind(complex_result) == kind(complex_x))
  call require_true('atanh complex argument reaches bounded result', &
       aimag(complex_result) >= -1.6_RK .and. aimag(complex_result) <= 1.6_RK)
  write(*,'(a)') 'INTRINSICS 16.9.D ATANH ARGUMENTS OK'
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
end program i169d_atanh_arguments
