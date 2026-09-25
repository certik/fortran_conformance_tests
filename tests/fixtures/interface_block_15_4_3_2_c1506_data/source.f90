program interface_block_c1506_data_control
  implicit none
  interface
    subroutine s()
      integer :: x
      data x /1/
    end subroutine s
  end interface
  print '(a)', 'INTERFACE BLOCK C1506 DATA CONTROL OK'
end program interface_block_c1506_data_control
