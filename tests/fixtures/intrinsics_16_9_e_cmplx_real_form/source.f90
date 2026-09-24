program i169e_cmplx_real_form
  implicit none
  integer, parameter :: rk = selected_real_kind(10)
  complex(kind=rk) :: a, b, boz_pair
  a = cmplx(3, -2.0, kind=rk)
  b = cmplx(4.0_rk, 5, kind=rk)
  boz_pair = cmplx(z'3', z'4', kind=rk)
  call require_true('cmplx integer x real y exact', real(a, kind=rk) == 3.0_rk .and. aimag(a) == -2.0_rk)
  call require_true('cmplx real x integer y exact', real(b, kind=rk) == 4.0_rk .and. aimag(b) == 5.0_rk)
  call require_true('cmplx boz x y match real conversions', &
      real(boz_pair, kind=rk) == real(z'3', kind=rk) .and. aimag(boz_pair) == real(z'4', kind=rk))
  call require_true('cmplx real form kind constant', kind(cmplx(3, -2.0, kind=rk)) == rk)
  call require_true('cmplx components are real conversions', &
      real(a, kind=rk) == real(3, kind=rk) .and. aimag(a) == real(-2.0, kind=rk))
  write(*,'(a)') 'INTRINSICS 16.9.E CMPLX REAL FORM OK'
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
end program i169e_cmplx_real_form
