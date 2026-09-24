program i169g_cshift_absent_dim_default
  implicit none
  integer :: m(3,3), expected(3,3)
  m(1,:) = [1, 2, 3]
  m(2,:) = [4, 5, 6]
  m(3,:) = [7, 8, 9]
  expected(1,:) = [4, 5, 6]
  expected(2,:) = [7, 8, 9]
  expected(3,:) = [1, 2, 3]
  call require_true('absent dim acts as dim one', all(cshift(m, 1) == expected))
  call require_true('dim two would differ', any(cshift(m, 1, dim=2) /= expected))
  write(*,'(a)') 'INTRINSICS 16.9.G CSHIFT ABSENT DIM DEFAULT OK'
contains
  subroutine require_true(label, value)
    character(len=*), intent(in) :: label
    logical, intent(in) :: value
    if (.not. value) then
      write(*,'(a)') label
      error stop
    end if
  end subroutine require_true
end program i169g_cshift_absent_dim_default
