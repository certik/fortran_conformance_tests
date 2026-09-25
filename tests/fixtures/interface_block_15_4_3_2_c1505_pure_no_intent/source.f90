program interface_block_pure_control
  implicit none
  interface
    pure subroutine p(x)
      integer :: x
    end subroutine p
  end interface
  print '(a)', 'INTERFACE BLOCK PURE CONTROL OK'
end program interface_block_pure_control
