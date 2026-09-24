program i169e_cmplx_defaults
  implicit none
  complex :: z
  z = cmplx(-3)
  call require_true('cmplx absent y zero imaginary', real(z) == -3.0 .and. aimag(z) == 0.0)
  call require_true('cmplx absent kind default real kind', kind(cmplx(-3)) == kind(cmplx(0.0, 0.0)))
  call require_true('cmplx result is complex assignable', real(z) == -3.0)
  write(*,'(a)') 'INTRINSICS 16.9.E CMPLX ABSENT Y OK'
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
end program i169e_cmplx_defaults
