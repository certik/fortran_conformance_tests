program i169f_cospi_elemental
  implicit none
  real(kind=kind(0.0d0)) :: x(3)
  x = [0.0d0, 0.25d0, 1.0d0]
  call require_true('cospi elemental array extent direct', size(cospi(x)) == 3)
  call require_true('cospi elemental array shape direct', all(shape(cospi(x)) == shape(x)))
  write(*,'(a)') 'INTRINSICS 16.9.F COSPI ELEMENTAL OK'
contains
  subroutine require_true(label, value)
    character(len=*), intent(in) :: label
    logical, intent(in) :: value
    if (.not. value) then
      write(*,'(a)') label
      error stop
    end if
  end subroutine require_true
end program i169f_cospi_elemental
