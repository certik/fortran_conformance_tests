program i169e_cmplx_complex_form
  implicit none
  integer, parameter :: rk = selected_real_kind(10)
  complex(kind=rk) :: z, result
  z = cmplx(1.25_rk, -2.5_rk, kind=rk)
  result = cmplx(z, kind=rk)
  call require_true('cmplx complex x argument', real(result, kind=rk) == 1.25_rk)
  call require_true('cmplx complex kind constant', kind(cmplx(z, kind=rk)) == rk)
  call require_true('cmplx result complex type and kind', kind(cmplx(1.0_rk, 2.0_rk, kind=rk)) == rk)
  call require_true('cmplx complex decomposes to parts', aimag(result) == -2.5_rk)
  write(*,'(a)') 'INTRINSICS 16.9.E CMPLX COMPLEX PARTS OK'
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
end program i169e_cmplx_complex_form
