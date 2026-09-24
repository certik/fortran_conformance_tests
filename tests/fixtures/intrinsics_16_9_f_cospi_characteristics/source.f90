program i169f_cospi_characteristics
  implicit none
  real(kind=kind(0.0d0)) :: scalar_x, vector_x(3)
  scalar_x = 0.25d0
  vector_x = [0.0d0, 0.25d0, 1.0d0]
  call require_true('cospi result same kind direct', kind(cospi(scalar_x)) == kind(scalar_x))
  call require_true('cospi result shape direct', all(shape(cospi(vector_x)) == shape(vector_x)))
  write(*,'(a)') 'INTRINSICS 16.9.F COSPI CHARACTERISTICS OK'
contains
  subroutine require_true(label, value)
    character(len=*), intent(in) :: label
    logical, intent(in) :: value
    if (.not. value) then
      write(*,'(a)') label
      error stop
    end if
  end subroutine require_true
end program i169f_cospi_characteristics
