program i169f_cospi_argument
  implicit none
  real(kind=kind(0.0d0)) :: x
  x = 0.25d0
  call require_true('cospi real x accepted with same kind', kind(cospi(x)) == kind(x))
  write(*,'(a)') 'INTRINSICS 16.9.F COSPI ARGUMENT OK'
contains
  subroutine require_true(label, value)
    character(len=*), intent(in) :: label
    logical, intent(in) :: value
    if (.not. value) then
      write(*,'(a)') label
      error stop
    end if
  end subroutine require_true
end program i169f_cospi_argument
