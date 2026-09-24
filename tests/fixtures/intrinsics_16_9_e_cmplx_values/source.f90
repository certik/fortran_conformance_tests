program i169e_cmplx_values
  implicit none
  integer, parameter :: rk = selected_real_kind(10)
  complex :: defaulted
  complex(kind=rk) :: from_parts, from_complex
  complex(kind=rk) :: z
  defaulted = cmplx(-3)
  z = cmplx(1.25_rk, -2.5_rk, kind=rk)
  from_complex = cmplx(z, kind=rk)
  from_parts = cmplx(3, -2.0, kind=rk)
  call require_true('cmplx absent y supplies zero', real(defaulted) == -3.0 .and. aimag(defaulted) == 0.0)
  call require_true('cmplx absent kind supplies default', kind(cmplx(-3)) == kind(cmplx(0.0, 0.0)))
  call require_true('cmplx complex x decomposes', real(from_complex, kind=rk) == 1.25_rk .and. aimag(from_complex) == -2.5_rk)
  call require_true('cmplx components from real conversions', &
      real(from_parts, kind=rk) == real(3, kind=rk) .and. aimag(from_parts) == real(-2.0, kind=rk))
  write(*,'(a)') 'INTRINSICS 16.9.E CMPLX VALUES OK'
contains
  subroutine require_true(label, value)
    character(len=*), intent(in) :: label
    logical, intent(in) :: value
    if (.not. value) then
      write(*,'(a)') label
      error stop
    end if
  end subroutine require_true
  subroutine require_false(label, value)
    character(len=*), intent(in) :: label
    logical, intent(in) :: value
    if (value) then
      write(*,'(a)') label
      error stop
    end if
  end subroutine require_false
end program i169e_cmplx_values
