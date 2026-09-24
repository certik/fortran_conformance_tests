program i169g_dble_elemental_array
  implicit none
  integer :: input(3)
  double precision :: output(3)
  input = [-3, 0, 5]
  output = dble(input)
  call require_true('elemental array shape direct', all(shape(dble(input)) == [3]))
  call require_true('elemental element values', all(output == [-3.0d0, 0.0d0, 5.0d0]))
  write(*,'(a)') 'INTRINSICS 16.9.G DBLE ELEMENTAL ARRAY OK'
contains
  subroutine require_true(label, value)
    character(len=*), intent(in) :: label
    logical, intent(in) :: value
    if (.not. value) then
      write(*,'(a)') label
      error stop
    end if
  end subroutine require_true
end program i169g_dble_elemental_array
